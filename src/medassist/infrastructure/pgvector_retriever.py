"""Implementa embeddings via Ollama e recuperação semântica via pgvector."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Sequence

from medassist.application.retrieval import (
    EmbeddingProvider,
    RetrievedChunk,
    RetrievalResponse,
)


EXPECTED_EMBEDDING_DIMENSIONS = 768


class RetrievalError(RuntimeError):
    """Indica falha ao gerar embeddings ou consultar a base vetorial."""


class OllamaEmbeddingProvider:
    """Gera embeddings locais usando o endpoint HTTP do Ollama."""

    def __init__(
        self,
        model: str = "embeddinggemma:300m",
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 120.0,
    ) -> None:
        if not model.strip():
            raise ValueError("model não pode estar vazio")
        if not base_url.strip():
            raise ValueError("base_url não pode estar vazia")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds deve ser maior que zero")

        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Solicita e valida os embeddings de uma sequência de textos."""
        if not texts or any(not text.strip() for text in texts):
            raise ValueError("texts deve conter textos não vazios")

        body = json.dumps(
            {"model": self.model, "input": list(texts)},
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.base_url}/api/embed",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as error:
            raise RetrievalError(
                "Não foi possível gerar o embedding da consulta"
            ) from error
        except json.JSONDecodeError as error:
            raise RetrievalError(
                "O Ollama retornou JSON inválido para o embedding"
            ) from error

        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise RetrievalError("Quantidade inesperada de embeddings")

        for embedding in embeddings:
            if (
                not isinstance(embedding, list)
                or len(embedding) != EXPECTED_EMBEDDING_DIMENSIONS
            ):
                raise RetrievalError("Dimensão inesperada do embedding")

        return embeddings


class PgVectorRetriever:
    """Recupera chunks do PostgreSQL ordenados por similaridade semântica."""

    def __init__(
        self,
        connection: Any,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.connection = connection
        self.embedding_provider = embedding_provider

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        minimum_similarity: float = 0.55,
    ) -> RetrievalResponse:
        """Busca evidências e retorna vazio quando nenhuma supera o limiar."""
        if not query.strip():
            raise ValueError("query não pode estar vazia")
        if limit <= 0:
            raise ValueError("limit deve ser maior que zero")
        if not 0.0 <= minimum_similarity <= 1.0:
            raise ValueError("minimum_similarity deve estar entre 0.0 e 1.0")

        embedding = self.embedding_provider.embed([query])[0]
        vector = json.dumps(embedding, separators=(",", ":"))

        statement = """
            WITH query_vector AS (
                SELECT %s::vector AS embedding
            )
            SELECT
                chunk.external_id,
                document.external_id,
                chunk.content,
                1 - (chunk.embedding <=> query_vector.embedding) AS similarity,
                document.collection,
                document.source,
                document.url
            FROM knowledge_chunks AS chunk
            JOIN knowledge_documents AS document
                ON document.document_id = chunk.document_id
            CROSS JOIN query_vector
            WHERE chunk.embedding IS NOT NULL
              AND 1 - (chunk.embedding <=> query_vector.embedding) >= %s
            ORDER BY chunk.embedding <=> query_vector.embedding
            LIMIT %s
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    statement,
                    (vector, minimum_similarity, limit),
                )
                rows = cursor.fetchall()
        except Exception as error:
            raise RetrievalError("Falha ao consultar a base vetorial") from error

        results = tuple(
            RetrievedChunk(
                chunk_id=row[0],
                document_id=row[1],
                content=row[2],
                similarity=float(row[3]),
                collection=row[4],
                source=row[5],
                url=row[6],
            )
            for row in rows
        )
        return RetrievalResponse(
            query=query,
            results=results,
            minimum_similarity=minimum_similarity,
        )

