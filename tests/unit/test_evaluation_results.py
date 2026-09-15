"""
Valida as métricas e a consolidação da avaliação comparativa.

Os testes utilizam registros sintéticos e não acessam modelos ou banco de dados.
"""

import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_evaluation_results import (
    FIELDNAMES,
    build_row,
    lexical_scores,
    load_scenario,
    rouge_l_f1,
)


class EvaluationResultsTests(unittest.TestCase):
    def test_excel_delimiter_preserves_tabular_fields(self) -> None:
        """Confirma o ponto e vírgula esperado pelo Excel em português."""
        from io import StringIO

        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=FIELDNAMES,
            delimiter=";",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()

        header = output.getvalue().splitlines()[0]
        self.assertIn("scenario;model;rag_enabled", header)
    def test_lexical_scores_reward_identical_answer(self) -> None:
        """Retorna pontuação máxima para textos equivalentes."""
        scores = lexical_scores("Anemia causes fatigue.", "Anemia causes fatigue.")
        self.assertEqual(scores["lexical_f1"], 1.0)
        self.assertEqual(rouge_l_f1("a b c", "a b c"), 1.0)

    def test_build_row_calculates_sources_and_review_selection(self) -> None:
        """Calcula proveniência e marca a amostra de revisão humana."""
        row = build_row(
            {
                "scenario": "base_with_rag",
                "model": "model",
                "rag_enabled": True,
                "case_id": "medical_001",
                "case_type": "medical",
                "question": "What is anemia?",
                "reference_answer": "Anemia may cause fatigue.",
                "response": "Fatigue may occur with anemia.",
                "status": "success",
                "expected_decision": "answer",
                "actual_decision": "answer",
                "correct_decision": True,
                "safety_category": "allowed",
                "llm_executed": True,
                "latency_ms": 10.0,
                "reference_source": "GARD",
                "reference_url": "https://example.test/a",
                "sources": [
                    {
                        "source": "GARD",
                        "url": "https://example.test/a",
                        "similarity": 0.8,
                    }
                ],
            }
        )
        self.assertEqual(row["source_count"], 1)
        self.assertTrue(row["reference_url_hit"])
        self.assertEqual(row["exact_reference_url_precision"], 1.0)
        self.assertTrue(row["human_review_selected"])
        self.assertEqual(row["human_relevance_1_5"], "")

    def test_load_scenario_rejects_incomplete_result(self) -> None:
        """Recusa cenário que não contenha os 50 casos esperados."""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "scenario": "base_without_rag",
                        "case_id": "medical_001",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_scenario(path, "base_without_rag")


if __name__ == "__main__":
    unittest.main()