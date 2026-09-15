#!/usr/bin/env python3
"""Monta o contexto de paciente e RAG que será fornecido ao LLM."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg

from medassist.application.context_builder import (
    build_generation_context,
)
from medassist.infrastructure.config import load_env_file
from medassist.infrastructure.langchain_retriever import (
    LangChainPgVectorRetriever,
)
from medassist.infrastructure.pgvector_retriever import (
    OllamaEmbeddingProvider,
    PgVectorRetriever,
)
from medassist.infrastructure.postgres_patient_repository import (
    PostgresPatientRepository,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Lê o paciente, a pergunta e os parâmetros de recuperação."""
    parser = argparse.ArgumentParser(
        description="Monta o contexto estruturado do MedAssist."
    )
    parser.add_argument(
        "patient_id",
        help="Identificador sintético no formato PAT-000",
    )
    parser.add_argument(
        "query",
        help="Pergunta usada para recuperar conhecimento médico",
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
    """Consulta paciente e RAG e apresenta o contexto consolidado."""
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
        patient_context = PostgresPatientRepository(
            connection
        ).get_by_id(args.patient_id)

        if patient_context is None:
            print(
                f"Paciente {args.patient_id.upper()} não encontrado."
            )
            return

        langchain_retriever = LangChainPgVectorRetriever(
            retriever=PgVectorRetriever(
                connection,
                embedding_provider,
            ),
            limit=args.limit,
            minimum_similarity=args.minimum_similarity,
        )

        documents = langchain_retriever.invoke(args.query)

    generation_context = build_generation_context(
        patient_context,
        documents,
    )

    print("=" * 80)
    print("CONTEXTO QUE SERÁ FORNECIDO AO LLM")
    print("=" * 80)
    print(generation_context.render())

    print()
    print("=" * 80)
    print("RESUMO")
    print("=" * 80)
    print(f"Patient ID: {generation_context.patient_id}")
    print(f"Evidências recuperadas: {len(documents)}")
    print(f"Fontes estruturadas: {len(generation_context.sources)}")
    print(
        "Possui evidência suficiente:",
        generation_context.has_evidence,
    )


if __name__ == "__main__":
    main()