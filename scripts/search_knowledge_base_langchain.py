#!/usr/bin/env python3
"""Executa uma busca vetorial usando a interface BaseRetriever do LangChain."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg

from medassist.infrastructure.config import load_env_file
from medassist.infrastructure.langchain_retriever import (
    LangChainPgVectorRetriever,
)
from medassist.infrastructure.pgvector_retriever import (
    OllamaEmbeddingProvider,
    PgVectorRetriever,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Lê a pergunta e os parâmetros da busca."""
    parser = argparse.ArgumentParser(
        description="Executa o retriever do MedAssist pelo LangChain."
    )
    parser.add_argument(
        "query",
        help="Pergunta a ser pesquisada",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--minimum-similarity",
        type=float,
        default=0.55,
    )
    return parser.parse_args()


def main() -> None:
    """Monta o retriever, executa invoke e exibe os Documents."""
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
        pgvector_retriever = PgVectorRetriever(
            connection,
            embedding_provider,
        )

        langchain_retriever = LangChainPgVectorRetriever(
            retriever=pgvector_retriever,
            limit=args.limit,
            minimum_similarity=args.minimum_similarity,
        )

        documents = langchain_retriever.invoke(args.query)

    print(f"Pergunta: {args.query}")
    print(f"Documents recuperados: {len(documents)}")

    if not documents:
        print("Nenhuma evidência suficiente foi recuperada.")
        return

    for position, document in enumerate(
        documents,
        start=1,
    ):
        print("=" * 80)
        print(f"Document: {position}")
        print(
            "Similaridade:",
            f"{document.metadata['similarity']:.4f}",
        )
        print(
            "Coleção:",
            document.metadata["collection"],
        )
        print(
            "Fonte:",
            document.metadata["source"],
        )
        print(
            "URL:",
            document.metadata["url"],
        )
        print(
            "Chunk:",
            document.metadata["chunk_id"],
        )
        print(document.page_content)


if __name__ == "__main__":
    main()