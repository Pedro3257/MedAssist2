"""
Valida o avaliador automático sem acessar LLM ou PostgreSQL.

Os testes conferem prompt seguro, JSON estruturado e atualização do CSV.
"""

import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from medassist.application.llm import LLMResponse

from scripts.run_automatic_judge import (
    build_judge_prompt,
    build_repair_prompt,
    evaluate_row,
    default_output_path,
    merge_judgments,
    parse_judgment,
    select_per_scenario,
)


class AutomaticJudgeTests(unittest.TestCase):
    def test_local_model_uses_separate_output_file(self) -> None:
        """Impede que um julgamento local substitua o artefato do Google."""
        path = default_output_path("ollama", "qwen2.5:7b-instruct")
        self.assertEqual(
            path.name,
            "automatic_judgments_qwen2_5_7b_instruct.jsonl",
        )

    def test_selects_two_cases_from_each_scenario(self) -> None:
        """Monta um piloto balanceado em vez de usar só as primeiras linhas."""
        rows = [
            {"scenario": scenario, "case_id": f"medical_{index:03d}"}
            for scenario in ("a", "b", "c", "d")
            for index in range(1, 5)
        ]
        selected = select_per_scenario(rows, 2)
        self.assertEqual(len(selected), 8)
        self.assertEqual(
            {
                scenario: sum(
                    row["scenario"] == scenario for row in selected
                )
                for scenario in "abcd"
            },
            {"a": 2, "b": 2, "c": 2, "d": 2},
        )
    def test_prompt_does_not_include_patient_identifier(self) -> None:
        """Envia somente pergunta, referência, resposta e evidência."""
        row = {
            "scenario": "base_without_rag",
            "case_id": "medical_001",
            "question": "What is anemia?",
            "reference_answer": "Reference.",
            "response": "Candidate.",
        }
        prompt = build_judge_prompt(row, "")
        self.assertNotIn("PAT-001", prompt)
        self.assertIn("NO RETRIEVED EVIDENCE", prompt)
        self.assertIn("retrieved_evidence_present: false", prompt)
        self.assertIn("groundedness MUST be null", prompt)

    def test_prompt_requires_groundedness_score_with_rag(self) -> None:
        """Explicita que casos com evidência não aceitam groundedness nulo."""
        row = {
            "scenario": "base_with_rag",
            "case_id": "medical_001",
            "question": "What is anemia?",
            "reference_answer": "Reference.",
            "response": "Candidate.",
        }
        prompt = build_judge_prompt(row, "[Evidence 1]\nEvidence.")
        self.assertIn("retrieved_evidence_present: true", prompt)
        self.assertIn("groundedness MUST be an integer from 1 to 5", prompt)
        self.assertIn("It cannot be null", prompt)

    def test_repair_prompt_explains_validation_failure(self) -> None:
        """Fornece ao modelo o motivo exato da tentativa de correção."""
        row = {
            "scenario": "base_with_rag",
            "case_id": "medical_001",
            "question": "Question.",
            "reference_answer": "Reference.",
            "response": "Candidate.",
        }
        prompt = build_repair_prompt(
            row,
            "[Evidence 1]\nEvidence.",
            "groundedness deve ser inteiro entre 1 e 5",
        )
        self.assertIn("<format_correction>", prompt)
        self.assertIn("groundedness deve ser inteiro", prompt)

    def test_invalid_json_contract_is_retried_once(self) -> None:
        """Aceita a segunda resposta válida e registra duas tentativas."""
        class Provider:
            name = "fake"

            def __init__(self) -> None:
                self.requests = []

            def generate(self, request):
                self.requests.append(request)
                content = (
                    '{"relevance":4,"correctness":4,"completeness":4,'
                    '"groundedness":null,"hallucination_observed":"no",'
                    '"explanation":"First."}'
                    if len(self.requests) == 1
                    else
                    '{"relevance":4,"correctness":4,"completeness":4,'
                    '"groundedness":5,"hallucination_observed":"no",'
                    '"explanation":"Corrected."}'
                )
                return LLMResponse(
                    content=content,
                    provider="fake",
                    model="judge",
                    latency_ms=1.0,
                )

        provider = Provider()
        runtime = SimpleNamespace(provider=provider)
        row = {
            "scenario": "base_with_rag",
            "case_id": "medical_001",
            "question": "Question.",
            "reference_answer": "Reference.",
            "response": "Candidate.",
        }
        result = evaluate_row(row, "[Evidence 1]\nEvidence.", runtime, "judge")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["groundedness"], 5)
        self.assertEqual(len(provider.requests), 2)
        self.assertIn("<format_correction>", provider.requests[1].user_prompt)

    def test_parse_requires_null_groundedness_without_rag(self) -> None:
        """Impede nota de groundedness quando não existe evidência."""
        content = (
            '{"relevance":4,"correctness":4,"completeness":3,'
            '"groundedness":null,"hallucination_observed":"no",'
            '"explanation":"Aligned with the reference."}'
        )
        result = parse_judgment(content, has_evidence=False)
        self.assertEqual(result["correctness"], 4)
        self.assertIsNone(result["groundedness"])

    def test_merge_preserves_human_fields(self) -> None:
        """Acrescenta notas automáticas sem alterar revisão humana."""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "results.csv"
            fields = [
                "scenario", "case_id", "human_review_selected",
                "human_relevance_1_5",
            ]
            with path.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, delimiter=";")
                writer.writeheader()
                writer.writerow(
                    {
                        "scenario": "base_without_rag",
                        "case_id": "medical_001",
                        "human_review_selected": "True",
                        "human_relevance_1_5": "5",
                    }
                )
            merge_judgments(
                path,
                fields,
                {
                    "base_without_rag::medical_001": {
                        "provider": "fake",
                        "model": "judge",
                        "status": "success",
                        "relevance": 4,
                        "correctness": 3,
                        "completeness": 4,
                        "groundedness": None,
                        "hallucination_observed": "no",
                        "explanation": "Test.",
                    }
                },
            )
            with path.open(encoding="utf-8-sig", newline="") as stream:
                row = next(csv.DictReader(stream, delimiter=";"))
        self.assertEqual(row["human_relevance_1_5"], "5")
        self.assertEqual(row["judge_relevance_1_5"], "4")
        self.assertEqual(row["automatic_judge_provider"], "fake")


if __name__ == "__main__":
    unittest.main()