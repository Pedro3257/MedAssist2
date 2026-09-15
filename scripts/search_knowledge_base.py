#!/usr/bin/env python3
"""Executa uma busca semântica local na base vetorial do MedAssist."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg

from medassist.infrastructure.config import load_env_file
from medassist.infrastructure.pgvector_retriever import (
    OllamaEmbeddingProvider,
    PgVectorRetriever,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Lê a pergunta e os parâmetros da recuperação."""
    parser = argparse.ArgumentParser(
        description="Busca chunks médicos por similaridade semântica."
    )
    parser.add_argument("query", help="Pergunta a pesquisar")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--minimum-similarity", type=float, default=0.55)
    return parser.parse_args()


def main() -> None:
    """Conecta os providers, executa a busca e imprime as fontes."""
    args = parse_args()
    load_env_file(PROJECT_ROOT / ".env")

    embedding_provider = OllamaEmbeddingProvider(
        model=os.getenv(
            "OLLAMA_EMBEDDING_MODEL",
            "embeddinggemma:300m",
        ),
        base_url=os.getenv(
            "OLLAMA_BASE_URL",
            "http://127.0.0.1:11434",
        ),
    )

    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "medassist"),
        user=os.getenv("POSTGRES_USER", "medassist"),
        password=os.environ["POSTGRES_PASSWORD"],
    ) as connection:
        response = PgVectorRetriever(
            connection,
            embedding_provider,
        ).search(
            args.query,
            limit=args.limit,
            minimum_similarity=args.minimum_similarity,
        )

    print(f"Pergunta: {response.query}")
    print(f"Limiar mínimo: {response.minimum_similarity:.4f}")

    if response.abstained:
        print("Nenhuma evidência suficiente foi recuperada.")
        return

    for position, result in enumerate(response.results, start=1):
        print("=" * 80)
        print(f"Resultado: {position}")
        print(f"Similaridade: {result.similarity:.4f}")
        print(f"Coleção: {result.collection}")
        print(f"Fonte: {result.source or 'não informada'}")
        print(f"URL: {result.url or 'não informada'}")
        print(f"Chunk: {result.chunk_id}")
        print(result.content)


if __name__ == "__main__":
    main()
