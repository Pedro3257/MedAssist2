"""
Valida o executor comparativo sem chamar Ollama ou PostgreSQL.

Os testes cobrem segurança, geração direta, retomada e integridade dos cenários.
"""

import json
import tempfile
import unittest
from pathlib import Path

from medassist.application.llm import LLMProvider, LLMRequest, LLMResponse
from medassist.providers.factory import LLMRuntime
from scripts.run_comparative_evaluation import (
    SCENARIOS,
    completed_case_ids,
    consolidated_stats,
    evaluate_without_rag,
    evaluate_with_rag,
    print_progress,
    run_cases,
)
from medassist.infrastructure.pgvector_retriever import RetrievalError


class FakeProvider(LLMProvider):
    """Retorna uma resposta fixa e conta chamadas realizadas."""

    def __init__(self) -> None:
        self.calls = 0

    @property
    def name(self) -> str:
        return "fake"

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        return LLMResponse(
            content="Educational answer.",
            provider="fake",
            model=request.model,
            latency_ms=10.0,
            input_tokens=8,
            output_tokens=4,
            finish_reason="stop",
        )


def case(question: str, expected: str = "answer") -> dict[str, object]:
    """Cria um caso mínimo compatível com o executor."""
    return {
        "case_id": "case-001",
        "case_type": "medical" if expected == "answer" else "safety",
        "patient_id": "PAT-001",
        "question": question,
        "reference_answer": "Reference.",
        "expected_decision": expected,
        "expected_safety_category": "allowed",
    }


class ComparativeEvaluationTests(unittest.TestCase):
    def test_declares_four_expected_scenarios(self) -> None:
        """Mantém os quatro cenários exigidos pelo cronograma."""
        self.assertEqual(len(SCENARIOS), 4)
        self.assertEqual(sum(item.use_rag for item in SCENARIOS.values()), 2)

    def test_safety_case_does_not_call_model(self) -> None:
        """Bloqueia dosagem antes da execução da LLM."""
        provider = FakeProvider()
        runtime = LLMRuntime(provider=provider, model="ignored")
        item = case("What exact dosage should I take?", "blocked")

        result = evaluate_without_rag(
            item, SCENARIOS["base_without_rag"], runtime
        )

        self.assertEqual(result["actual_decision"], "blocked")
        self.assertFalse(result["llm_executed"])
        self.assertEqual(provider.calls, 0)

    def test_medical_case_uses_selected_model(self) -> None:
        """Gera resposta médica com o modelo definido pelo cenário."""
        provider = FakeProvider()
        runtime = LLMRuntime(provider=provider, model="ignored")

        result = evaluate_without_rag(
            case("What is anemia?"),
            SCENARIOS["base_without_rag"],
            runtime,
        )

        self.assertEqual(result["model"], "llama3.2:1b")
        self.assertEqual(result["actual_decision"], "answer")
        self.assertEqual(provider.calls, 1)

    def test_resume_skips_completed_case(self) -> None:
        """Não repete um caso já gravado com sucesso."""
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result.jsonl"
            calls = []

            def evaluator(item: dict[str, object]) -> dict[str, object]:
                calls.append(str(item["case_id"]))
                return {"case_id": item["case_id"], "status": "success"}

            items = [case("What is anemia?")]
            run_cases(items, output, evaluator)
            stats = run_cases(items, output, evaluator, resume=True)

            self.assertEqual(stats["skipped"], 1)
            self.assertEqual(calls, ["case-001"])
            self.assertEqual(completed_case_ids(output), {"case-001"})
            self.assertEqual(len(output.read_text().splitlines()), 1)

    def test_progress_bar_reports_counts(self) -> None:
        """Apresenta progresso sem exigir biblioteca externa."""
        from contextlib import redirect_stdout
        from io import StringIO

        output = StringIO()
        with redirect_stdout(output):
            print_progress(
                2,
                4,
                {"success": 2, "error": 0, "skipped": 0},
                "medical_002",
                "success",
            )

        rendered = output.getvalue()
        self.assertIn("2/4", rendered)
        self.assertIn("50.00%", rendered)
        self.assertIn("medical_002 success", rendered)

    def test_rag_retrieval_error_becomes_case_error(self) -> None:
        """Registra timeout do embedding sem encerrar todo o lote."""
        class FailingGraph:
            def invoke(self, state: dict[str, object]) -> dict[str, object]:
                raise RetrievalError("embedding unavailable")

        result = evaluate_with_rag(
            case("What is anemia?"),
            SCENARIOS["base_with_rag"],
            FailingGraph(),
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "RetrievalError")
        self.assertFalse(result["llm_executed"])

    def test_summary_consolidates_resumed_results(self) -> None:
        """Conta sucessos e erros acumulados por case_id único."""
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result.jsonl"
            output.write_text(
                "\n".join(
                    (
                        json.dumps({"case_id": "one", "status": "success"}),
                        json.dumps({"case_id": "two", "status": "error"}),
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            stats = consolidated_stats(output, {"one", "two"})

        self.assertEqual(stats["completed"], 2)
        self.assertEqual(stats["success"], 1)
        self.assertEqual(stats["error"], 1)


if __name__ == "__main__":
    unittest.main()