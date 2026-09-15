#!/usr/bin/env python3
"""
Executa o workflow LangGraph completo com auditoria no PostgreSQL.

O script conecta paciente, RAG, provider, validação humana e auditoria.
A transação é confirmada ao sair normalmente do contexto da conexão.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg

# Permite executar a CLI diretamente da raiz sem configurar PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
from medassist.application.contextual_answer import (
    ContextualAnswerService,
)
from medassist.application.graph_workflow import (
    build_medassist_graph,
)
from medassist.infrastructure.config import load_env_file
from medassist.infrastructure.langchain_retriever import (
    LangChainPgVectorRetriever,
)
from medassist.infrastructure.pgvector_retriever import (
    OllamaEmbeddingProvider,
    PgVectorRetriever,
)
from medassist.infrastructure.postgres_audit_repository import (
    PostgresAuditRepository,
)
from medassist.infrastructure.postgres_patient_repository import (
    PostgresPatientRepository,
)
from medassist.providers.factory import create_llm_runtime


ENV_FILE = PROJECT_ROOT / ".env"


def parse_args() -> argparse.Namespace:
    """Lê paciente, pergunta e parâmetros da execução."""
    parser = argparse.ArgumentParser(
        description=(
            "Executa o workflow LangGraph auditado do MedAssist."
        )
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
        help="Quantidade máxima de evidências",
    )
    parser.add_argument(
        "--minimum-similarity",
        type=float,
        default=0.55,
        help="Similaridade mínima entre 0 e 1",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=384,
        help="Quantidade máxima de tokens da resposta",
    )
    return parser.parse_args()


def print_result(result: dict[str, object]) -> None:
    """Apresenta somente o resultado final e sua proveniência."""
    print("=" * 80)
    print("RESULTADO DO LANGGRAPH")
    print("=" * 80)
    print(f"Correlation ID: {result.get('correlation_id')}")
    print(f"Rota final: {result.get('route')}")
    print(
        "Validação humana:",
        result.get("requires_human_validation", False),
    )
    print(
        "Audit event ID:",
        result.get("audit_event_id", "não persistido"),
    )

    latency_ms = result.get("latency_ms")

    if isinstance(latency_ms, (int, float)):
        print(f"Latência total: {latency_ms:.2f} ms")
    else:
        print("Latência total: não disponível")

    answer = result.get("answer")

    if answer is not None:
        print()
        print("=" * 80)
        print("RESPOSTA")
        print("=" * 80)
        print(answer.content)
    elif result.get("blocked_reason"):
        print()
        print("Orientação:")
        print(result["blocked_reason"])
    elif result.get("error"):
        print()
        print("Erro controlado:")
        print(result["error"])
    else:
        print()
        print("Nenhuma resposta clínica foi produzida.")

    print()
    print("=" * 80)
    print("AUDITORIA EM MEMÓRIA")
    print("=" * 80)

    for event in result.get("audit_events", []):
        print(
            f"{event['node']}: "
            f"{event['outcome']} - "
            f"{event['detail']}"
        )


def main() -> None:
    """Configura dependências, executa o grafo e confirma a transação."""
    args = parse_args()
    load_env_file(ENV_FILE)

    runtime = create_llm_runtime(ENV_FILE)

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
        host=os.getenv(
            "POSTGRES_HOST",
            "127.0.0.1",
        ),
        port=int(
            os.getenv(
                "POSTGRES_PORT",
                "5432",
            )
        ),
        dbname=os.getenv(
            "POSTGRES_DB",
            "medassist",
        ),
        user=os.getenv(
            "POSTGRES_USER",
            "medassist",
        ),
        password=os.environ["POSTGRES_PASSWORD"],
    ) as connection:
        patient_repository = PostgresPatientRepository(
            connection
        )

        retriever = LangChainPgVectorRetriever(
            retriever=PgVectorRetriever(
                connection,
                embedding_provider,
            ),
            limit=args.limit,
            minimum_similarity=(
                args.minimum_similarity
            ),
        )

        audit_repository = PostgresAuditRepository(
            connection
        )

        graph = build_medassist_graph(
            repository=patient_repository,
            retriever=retriever,
            answer_service=ContextualAnswerService(
                runtime.provider
            ),
            model=runtime.model,
            language_rewrite_model=(
                runtime.language_rewrite_model
            ),
            max_tokens=args.max_tokens,
            audit_repository=audit_repository,
            provider_name=runtime.provider.name,
            # Minimiza o prontuário somente para o provider remoto.
            minimize_remote_context=(
                runtime.provider.name == "google_ai"
            ),
        )

        result = graph.invoke(
            {
                "patient_id": args.patient_id,
                "question": args.question,
                "audit_events": [],
            }
        )

    print_result(result)


if __name__ == "__main__":
    main()