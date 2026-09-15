#!/usr/bin/env python3
"""Executa paciente, RAG, prompt LangChain e LLM em um único fluxo."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg

from medassist.application.context_builder import (
    build_generation_context,
)
from medassist.application.contextual_answer import (
    ContextualAnswerService,
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
from medassist.providers.factory import create_llm_runtime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"


def parse_args() -> argparse.Namespace:
    """Lê paciente, pergunta e parâmetros do fluxo contextual."""
    parser = argparse.ArgumentParser(
        description="Executa uma resposta contextualizada do MedAssist."
    )
    parser.add_argument(
        "patient_id",
        help="Paciente sintético no formato PAT-000",
    )
    parser.add_argument(
        "question",
        help="Pergunta enviada ao MedAssist",
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
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=384,
    )
    return parser.parse_args()


def main() -> None:
    """Executa o pipeline completo e apresenta resposta e proveniência."""
    args = parse_args()
    load_env_file(ENV_FILE)

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

        documents = langchain_retriever.invoke(
            args.question
        )

    generation_context = build_generation_context(
        patient_context,
        documents,
    )

    runtime = create_llm_runtime(ENV_FILE)

    answer = ContextualAnswerService(
        runtime.provider
    ).generate(
        question=args.question,
        context=generation_context,
        model=runtime.model,
        temperature=0.0,
        max_tokens=args.max_tokens,
        language_rewrite_model=runtime.language_rewrite_model,
    )

    print("=" * 80)
    print("RESPOSTA CONTEXTUALIZADA")
    print("=" * 80)
    print(answer.content)

    print()
    print("=" * 80)
    print("PROVENIÊNCIA")
    print("=" * 80)
    print(f"Patient ID: {answer.patient_id}")
    print(f"Provider: {answer.provider}")
    print(f"Model: {answer.model}")
    print(f"LLM executado: {answer.used_llm}")
    print(
        "Revisão de idioma executada:",
        answer.language_rewrite_performed,
    )
    print(f"Modelo revisor: {answer.rewrite_model or 'none'}")
    print(f"Abstenção: {answer.abstained}")
    print(f"Fontes recuperadas: {len(answer.sources)}")

    for source in answer.sources:
        print("-" * 80)
        print(f"Evidence: {source.position}")
        print(f"Similarity: {source.similarity:.4f}")
        print(f"Collection: {source.collection}")
        print(f"Source: {source.source or 'not informed'}")
        print(f"URL: {source.url or 'not informed'}")
        print(f"Chunk: {source.chunk_id}")


if __name__ == "__main__":
    main()