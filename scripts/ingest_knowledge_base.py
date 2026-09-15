#!/usr/bin/env python3
"""Gera embeddings com Ollama e carrega a base MedQuAD no PostgreSQL."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterator

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCUMENTS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "knowledge_documents.jsonl"
)
DEFAULT_CHUNKS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "knowledge_chunks.jsonl"
)
EXPECTED_DIMENSIONS = 768


def parse_args() -> argparse.Namespace:
    """Lê as opções de execução do pipeline de ingestão."""
    parser = argparse.ArgumentParser(
        description="Carrega documentos, chunks e embeddings no PostgreSQL."
    )
    parser.add_argument(
        "--documents",
        type=Path,
        default=DEFAULT_DOCUMENTS_PATH,
    )
    parser.add_argument(
        "--chunks",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limita chunks novos; útil para o teste piloto.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Carrega e valida superficialmente um arquivo JSONL."""
    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"JSON inválido em {path}, linha {line_number}: {error}"
                ) from error

    return records


def batched(
    records: list[dict[str, Any]],
    batch_size: int,
) -> Iterator[list[dict[str, Any]]]:
    """Divide os registros em lotes de tamanho previsível."""
    for start in range(0, len(records), batch_size):
        yield records[start : start + batch_size]


def connect_database() -> psycopg.Connection[Any]:
    """Abre a conexão usando as variáveis PostgreSQL do arquivo .env."""
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "medassist"),
        user=os.getenv("POSTGRES_USER", "medassist"),
        password=os.environ["POSTGRES_PASSWORD"],
    )


def insert_documents(
    connection: psycopg.Connection[Any],
    documents: list[dict[str, Any]],
) -> dict[str, int]:
    """Insere ou atualiza documentos e devolve seus IDs internos."""
    statement = """
        INSERT INTO knowledge_documents (
            external_id,
            collection,
            source,
            title,
            url,
            metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_id) DO UPDATE SET
            collection = EXCLUDED.collection,
            source = EXCLUDED.source,
            title = EXCLUDED.title,
            url = EXCLUDED.url,
            metadata = EXCLUDED.metadata
    """

    values = [
        (
            document["external_id"],
            document["collection"],
            document.get("source"),
            document["title"],
            document.get("url"),
            Jsonb(document.get("metadata", {})),
        )
        for document in documents
    ]

    with connection.cursor() as cursor:
        cursor.executemany(statement, values)
        cursor.execute(
            "SELECT external_id, document_id FROM knowledge_documents"
        )
        mapping = {
            external_id: document_id
            for external_id, document_id in cursor.fetchall()
        }

    connection.commit()
    return mapping


def existing_chunk_ids(
    connection: psycopg.Connection[Any],
) -> set[str]:
    """Identifica chunks já persistidos para permitir retomada segura."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT external_id FROM knowledge_chunks")
        return {row[0] for row in cursor.fetchall()}


def generate_embeddings(
    texts: list[str],
    base_url: str,
    model: str,
) -> list[list[float]]:
    """Solicita ao Ollama um vetor normalizado para cada texto do lote."""
    payload = json.dumps(
        {"model": model, "input": texts},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Não foi possível gerar embeddings pelo Ollama: {error}"
        ) from error

    embeddings = result.get("embeddings", [])
    if len(embeddings) != len(texts):
        raise RuntimeError("O Ollama retornou uma quantidade inesperada de vetores.")

    for embedding in embeddings:
        if len(embedding) != EXPECTED_DIMENSIONS:
            raise RuntimeError(
                "Dimensão inesperada: "
                f"esperado {EXPECTED_DIMENSIONS}, recebido {len(embedding)}."
            )

    return embeddings


def vector_literal(embedding: list[float]) -> str:
    """Converte o vetor para o formato textual aceito pelo pgvector."""
    return json.dumps(embedding, separators=(",", ":"))


def insert_chunk_batch(
    connection: psycopg.Connection[Any],
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
    document_ids: dict[str, int],
) -> None:
    """Persiste um lote de chunks e embeddings de maneira idempotente."""
    statement = """
        INSERT INTO knowledge_chunks (
            document_id,
            external_id,
            chunk_index,
            content,
            question,
            answer,
            token_count,
            embedding_model,
            embedding,
            metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector, %s)
        ON CONFLICT (external_id) DO UPDATE SET
            document_id = EXCLUDED.document_id,
            chunk_index = EXCLUDED.chunk_index,
            content = EXCLUDED.content,
            question = EXCLUDED.question,
            answer = EXCLUDED.answer,
            token_count = EXCLUDED.token_count,
            embedding_model = EXCLUDED.embedding_model,
            embedding = EXCLUDED.embedding,
            metadata = EXCLUDED.metadata
    """

    values = []
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        document_external_id = chunk["document_external_id"]
        if document_external_id not in document_ids:
            raise RuntimeError(
                f"Documento não encontrado: {document_external_id}"
            )

        values.append(
            (
                document_ids[document_external_id],
                chunk["external_id"],
                chunk["chunk_index"],
                chunk["content"],
                chunk.get("question"),
                chunk.get("answer"),
                chunk.get("token_count"),
                chunk["embedding_model"],
                vector_literal(embedding),
                Jsonb(chunk.get("metadata", {})),
            )
        )

    with connection.cursor() as cursor:
        cursor.executemany(statement, values)
    connection.commit()


def main() -> None:
    """Coordena a ingestão retomável da base de conhecimento."""
    args = parse_args()
    if args.batch_size <= 0:
        raise ValueError("--batch-size deve ser maior que zero.")
    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit deve ser maior que zero.")

    load_dotenv(PROJECT_ROOT / ".env")
    documents = read_jsonl(args.documents)
    chunks = read_jsonl(args.chunks)
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    embedding_model = os.getenv(
        "OLLAMA_EMBEDDING_MODEL",
        "embeddinggemma:300m",
    )

    with connect_database() as connection:
        document_ids = insert_documents(connection, documents)
        persisted_ids = existing_chunk_ids(connection)
        pending_chunks = [
            chunk for chunk in chunks if chunk["external_id"] not in persisted_ids
        ]

        if args.limit is not None:
            pending_chunks = pending_chunks[: args.limit]

        print(f"Documentos disponíveis: {len(document_ids)}")
        print(f"Chunks já existentes: {len(persisted_ids)}")
        print(f"Chunks selecionados nesta execução: {len(pending_chunks)}")
        print(f"Modelo de embeddings: {embedding_model}")

        processed = 0
        for batch in batched(pending_chunks, args.batch_size):
            embeddings = generate_embeddings(
                [chunk["content"] for chunk in batch],
                ollama_base_url,
                embedding_model,
            )
            insert_chunk_batch(
                connection,
                batch,
                embeddings,
                document_ids,
            )
            processed += len(batch)
            print(f"Progresso: {processed}/{len(pending_chunks)}")

    print("Ingestão concluída com sucesso.")


if __name__ == "__main__":
    main()
