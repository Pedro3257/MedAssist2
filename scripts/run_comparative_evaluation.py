#!/usr/bin/env python3
"""
Executa os quatro cenários reproduzíveis da avaliação comparativa.

O executor aplica a mesma política de segurança em todos os cenários, grava
cada resultado imediatamente e permite retomar execuções interrompidas.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Callable, Iterable

import psycopg

from medassist.application.contextual_answer import ContextualAnswerService
from medassist.application.graph_workflow import build_medassist_graph
from medassist.application.llm import LLMProviderError, LLMRequest
from medassist.application.prompts import SYSTEM_PROMPT_VERSION, get_system_prompt
from medassist.application.safety import evaluate_request
from medassist.infrastructure.config import load_env_file
from medassist.infrastructure.langchain_retriever import LangChainPgVectorRetriever
from medassist.infrastructure.pgvector_retriever import (
    OllamaEmbeddingProvider,
    PgVectorRetriever,
    RetrievalError,
)
from medassist.infrastructure.postgres_patient_repository import (
    PostgresPatientRepository,
)
from medassist.providers.factory import LLMRuntime, create_llm_runtime


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "processed" / "evaluation_cases.jsonl"
OUTPUT_DIR = ROOT / "reports" / "evidence"
ENV_PATH = ROOT / ".env"
EXPECTED_INPUT_SHA256 = (
    "D4E26501B1EC2F2708FA7D20C920B3A7B7ABB1AB0ADCC5CD4EF1D87F8515421E"
)


@dataclass(frozen=True, slots=True)
class Scenario:
    """Define modelo, uso de RAG e arquivo de saída de um cenário."""

    name: str
    model: str
    use_rag: bool


SCENARIOS = {
    "base_without_rag": Scenario("base_without_rag", "llama3.2:1b", False),
    "base_with_rag": Scenario("base_with_rag", "llama3.2:1b", True),
    "adjusted_without_rag": Scenario(
        "adjusted_without_rag", "medassist-local:1.0.0", False
    ),
    "adjusted_with_rag": Scenario(
        "adjusted_with_rag", "medassist-local:1.0.0", True
    ),
}


def sha256(path: Path) -> str:
    """Calcula a assinatura do conjunto sem carregá-lo inteiro na memória."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_cases(path: Path = INPUT_PATH) -> list[dict[str, object]]:
    """Valida assinatura, estrutura e unicidade dos 50 casos fixos."""
    if sha256(path) != EXPECTED_INPUT_SHA256:
        raise RuntimeError("evaluation_cases.jsonl não corresponde ao conjunto validado")

    cases = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    identifiers = [str(case.get("case_id", "")) for case in cases]

    if len(cases) != 50 or len(set(identifiers)) != 50 or "" in identifiers:
        raise RuntimeError("O conjunto deve conter 50 case_id únicos")
    return cases


def completed_case_ids(path: Path) -> set[str]:
    """Retorna casos concluídos que podem ser ignorados em uma retomada."""
    if not path.is_file():
        return set()
    completed = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        completed.add(str(item["case_id"]))
    return completed


def consolidated_stats(
    path: Path,
    selected_case_ids: set[str],
) -> dict[str, int]:
    """Conta o último resultado gravado de cada caso selecionado."""
    latest: dict[str, dict[str, object]] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            case_id = str(item["case_id"])
            if case_id in selected_case_ids:
                latest[case_id] = item
    return {
        "selected": len(selected_case_ids),
        "completed": len(latest),
        "success": sum(
            item.get("status") == "success" for item in latest.values()
        ),
        "error": sum(
            item.get("status") == "error" for item in latest.values()
        ),
    }


def common_result(case: dict[str, object], scenario: Scenario) -> dict[str, object]:
    """Monta metadados idênticos para todos os cenários."""
    return {
        "schema_version": "1.0.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "scenario": scenario.name,
        "model": scenario.model,
        "rag_enabled": scenario.use_rag,
        "case_id": case["case_id"],
        "case_type": case["case_type"],
        "patient_id": case["patient_id"],
        "question": case["question"],
        "reference_answer": case.get("reference_answer"),
        "expected_decision": case["expected_decision"],
        "expected_safety_category": case["expected_safety_category"],
        "original_id": case.get("original_id"),
        "focus": case.get("focus"),
        "question_type": case.get("question_type"),
        "reference_source": case.get("source"),
        "reference_url": case.get("url"),
        "system_prompt_version": SYSTEM_PROMPT_VERSION,
    }


def evaluate_without_rag(
    case: dict[str, object],
    scenario: Scenario,
    runtime: LLMRuntime,
    *,
    max_tokens: int = 384,
) -> dict[str, object]:
    """Executa segurança e, quando permitido, chama diretamente a LLM."""
    started_at = perf_counter()
    decision = evaluate_request(str(case["question"]))
    common = common_result(case, scenario)

    if not decision.allowed:
        actual_decision = "urgent" if decision.category == "urgent" else "blocked"
        return {
            **common,
            "status": "success",
            "provider": "safety",
            "actual_decision": actual_decision,
            "safety_category": decision.category,
            "correct_decision": actual_decision == case["expected_decision"],
            "llm_executed": False,
            "response": decision.reason,
            "sources": [],
            "latency_ms": round((perf_counter() - started_at) * 1000, 3),
        }

    try:
        response = runtime.provider.generate(
            LLMRequest(
                system_prompt=get_system_prompt(),
                user_prompt=str(case["question"]),
                model=scenario.model,
                temperature=0.0,
                max_tokens=max_tokens,
                correlation_id=f"evaluation-{scenario.name}-{case['case_id']}",
            )
        )
    except LLMProviderError as error:
        return {
            **common,
            "status": "error",
            "provider": runtime.provider.name,
            "actual_decision": "provider_error",
            "safety_category": decision.category,
            "correct_decision": False,
            "llm_executed": True,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "sources": [],
            "latency_ms": round((perf_counter() - started_at) * 1000, 3),
        }

    return {
        **common,
        "status": "success",
        "provider": response.provider,
        "actual_decision": "answer",
        "safety_category": decision.category,
        "correct_decision": case["expected_decision"] == "answer",
        "llm_executed": True,
        "response": response.content,
        "sources": [],
        "latency_ms": round((perf_counter() - started_at) * 1000, 3),
        "provider_latency_ms": round(response.latency_ms, 3),
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "finish_reason": response.finish_reason,
    }


def evaluate_with_rag(
    case: dict[str, object],
    scenario: Scenario,
    graph: object,
) -> dict[str, object]:
    """Executa o LangGraph completo e serializa resposta, fontes e decisão."""
    started_at = perf_counter()
    decision = evaluate_request(str(case["question"]))
    try:
        result = graph.invoke(
            {
                "patient_id": case["patient_id"],
                "question": case["question"],
                "audit_events": [],
            }
        )
    except RetrievalError as error:
        return {
            **common_result(case, scenario),
            "status": "error",
            "provider": "ollama_embeddings",
            "actual_decision": "retrieval_error",
            "safety_category": decision.category,
            "correct_decision": False,
            "llm_executed": False,
            "response": None,
            "sources": [],
            "latency_ms": round((perf_counter() - started_at) * 1000, 3),
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
    answer = result.get("answer")
    sources = []
    response_text = result.get("blocked_reason")
    provider = "safety" if not decision.allowed else "fallback"

    if answer is not None:
        response_text = answer.answer_text
        provider = answer.provider
        sources = [
            {
                "position": source.position,
                "collection": source.collection,
                "source": source.source,
                "url": source.url,
                "chunk_id": source.chunk_id,
                "similarity": source.similarity,
            }
            for source in answer.sources
        ]

    route = str(result.get("route", "provider_error"))
    expected = str(case["expected_decision"])
    normalized_route = "answer" if route == "human_validation" else route

    return {
        **common_result(case, scenario),
        "status": "error" if route == "provider_error" else "success",
        "provider": provider,
        "actual_decision": normalized_route,
        "graph_route": route,
        "safety_category": decision.category,
        "correct_decision": normalized_route == expected,
        "llm_executed": bool(answer is not None and answer.used_llm),
        "response": response_text,
        "sources": sources,
        "latency_ms": round((perf_counter() - started_at) * 1000, 3),
        "requires_human_validation": result.get(
            "requires_human_validation", False
        ),
        "error_type": result.get("error"),
    }


def run_cases(
    cases: Iterable[dict[str, object]],
    output_path: Path,
    evaluator: Callable[[dict[str, object]], dict[str, object]],
    *,
    resume: bool = False,
) -> dict[str, int]:
    """Grava cada caso imediatamente e preserva resultados já concluídos."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    skipped = completed_case_ids(output_path) if resume else set()
    mode = "a" if resume else "w"
    stats = {"selected": 0, "success": 0, "error": 0, "skipped": 0}

    with output_path.open(mode, encoding="utf-8", newline="\n") as stream:
        case_list = list(cases)
        for index, case in enumerate(case_list, start=1):
            stats["selected"] += 1
            if str(case["case_id"]) in skipped:
                stats["skipped"] += 1
                print_progress(
                    index,
                    len(case_list),
                    stats,
                    str(case["case_id"]),
                    "skipped",
                )
                continue
            result = evaluator(case)
            stream.write(json.dumps(result, ensure_ascii=False) + "\n")
            stream.flush()
            stats[str(result["status"])] += 1
            print_progress(
                index,
                len(case_list),
                stats,
                str(case["case_id"]),
                str(result["status"]),
            )
    return stats


def print_progress(
    current: int,
    total: int,
    stats: dict[str, int],
    case_id: str,
    status: str,
) -> None:
    """Atualiza uma barra ASCII com percentual e contadores da execução."""
    width = 30
    completed = round(width * current / total)
    bar = "#" * completed + "-" * (width - completed)
    percentage = current * 100 / total
    print(
        f"\r[{bar}] {current}/{total} {percentage:6.2f}% | "
        f"ok={stats['success']} erros={stats['error']} "
        f"ignorados={stats['skipped']} | {case_id} {status}",
        end="\n" if current == total else "",
        flush=True,
    )


def database_connection() -> psycopg.Connection:
    """Abre a conexão usada somente pelos cenários com RAG."""
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "medassist"),
        user=os.getenv("POSTGRES_USER", "medassist"),
        password=os.environ["POSTGRES_PASSWORD"],
    )


def build_rag_graph(
    connection: psycopg.Connection,
    runtime: LLMRuntime,
    scenario: Scenario,
    max_tokens: int,
) -> object:
    """Monta o grafo com paciente sintético, pgvector e modelo selecionado."""
    embedding_provider = OllamaEmbeddingProvider(
        model=os.getenv("OLLAMA_EMBEDDING_MODEL", "embeddinggemma:300m"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        timeout_seconds=float(
            os.getenv("OLLAMA_EMBEDDING_TIMEOUT_SECONDS", "300")
        ),
    )
    retriever = LangChainPgVectorRetriever(
        retriever=PgVectorRetriever(connection, embedding_provider),
        limit=3,
        minimum_similarity=0.55,
    )
    return build_medassist_graph(
        repository=PostgresPatientRepository(connection),
        retriever=retriever,
        answer_service=ContextualAnswerService(runtime.provider),
        model=scenario.model,
        language_rewrite_model=scenario.model,
        max_tokens=max_tokens,
        provider_name=runtime.provider.name,
        minimize_remote_context=False,
    )


def parse_args() -> argparse.Namespace:
    """Lê cenário, limite piloto e opção de retomada."""
    parser = argparse.ArgumentParser(description="Executa avaliação comparativa.")
    parser.add_argument("--scenario", choices=tuple(SCENARIOS), required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--case-id",
        help="Executa somente um case_id específico do conjunto fixo",
    )
    parser.add_argument("--max-tokens", type=int, default=384)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Configura o cenário, executa os casos e salva seu resumo."""
    args = parse_args()
    if args.limit is not None and args.limit <= 0:
        raise ValueError("limit deve ser maior que zero")
    if args.max_tokens <= 0:
        raise ValueError("max-tokens deve ser maior que zero")

    load_env_file(ENV_PATH)
    os.environ["LLM_PROVIDER"] = "ollama"
    runtime = create_llm_runtime(ENV_PATH)
    scenario = SCENARIOS[args.scenario]
    cases = load_cases()
    if args.case_id:
        cases = [case for case in cases if case["case_id"] == args.case_id]
        if not cases:
            raise ValueError(f"case-id não encontrado: {args.case_id}")
    if args.limit is not None:
        cases = cases[: args.limit]

    output_path = OUTPUT_DIR / f"evaluation_{scenario.name}.jsonl"

    if scenario.use_rag:
        with database_connection() as connection:
            graph = build_rag_graph(connection, runtime, scenario, args.max_tokens)
            evaluator = lambda case: evaluate_with_rag(case, scenario, graph)
            stats = run_cases(cases, output_path, evaluator, resume=args.resume)
    else:
        evaluator = lambda case: evaluate_without_rag(
            case, scenario, runtime, max_tokens=args.max_tokens
        )
        stats = run_cases(cases, output_path, evaluator, resume=args.resume)

    totals = consolidated_stats(
        output_path,
        {str(case["case_id"]) for case in cases},
    )
    summary = {
        **totals,
        "processed_this_run": stats["success"] + stats["error"],
        "skipped_this_run": stats["skipped"],
        "scenario": scenario.name,
        "model": scenario.model,
        "rag_enabled": scenario.use_rag,
        "input_sha256": EXPECTED_INPUT_SHA256,
        "output": output_path.relative_to(ROOT).as_posix(),
    }
    summary_path = output_path.with_suffix(".summary.json")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 1 if stats["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())