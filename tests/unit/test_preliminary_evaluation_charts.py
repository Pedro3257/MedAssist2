"""Testa a preparação das tabelas e gráficos preliminares da avaliação."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.build_preliminary_evaluation_charts import (
    SCENARIOS,
    build_rows,
    write_bar_chart,
    write_grouped_chart,
)


class PreliminaryEvaluationChartsTests(unittest.TestCase):
    """Valida os cálculos e a geração SVG sem dependências externas."""

    def setUp(self) -> None:
        """Cria um resumo mínimo com os quatro cenários obrigatórios."""
        self.summary = {
            scenario: {
                "total": 50,
                "success": 50,
                "error": 0,
                "correct_safety_decisions": 10,
                "safety_cases": 10,
                "mean_latency_ms": 1000 + index,
                "mean_lexical_f1": 0.1 + index / 10,
                "mean_reference_coverage": 0.2 + index / 10,
                "mean_rouge_l_f1": 0.15 + index / 10,
                "reference_url_hits": 8 if index >= 2 else 0,
                "medical_cases_with_sources": 10 if index >= 2 else 0,
            }
            for index, scenario in enumerate(SCENARIOS)
        }

    def test_build_rows_calculates_rates(self) -> None:
        """Calcula taxas de segurança e URL sem inventar zero para não aplicável."""
        rows = build_rows(self.summary)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["correct_safety_rate"], 1.0)
        self.assertIsNone(rows[0]["reference_url_hit_rate"])
        self.assertEqual(rows[2]["reference_url_hit_rate"], 0.8)

    def test_writers_create_valid_svg_roots(self) -> None:
        """Gera os dois tipos de gráfico com título e raiz SVG."""
        rows = build_rows(self.summary)
        with tempfile.TemporaryDirectory() as directory:
            grouped = Path(directory) / "grouped.svg"
            bars = Path(directory) / "bars.svg"
            write_grouped_chart(
                grouped,
                rows,
                (("mean_lexical_f1", "F1", "#2563EB"),),
                "Qualidade",
                "Pontuação",
                1.0,
            )
            write_bar_chart(
                bars,
                rows,
                "mean_latency_ms",
                "Latência",
                "Preliminar",
                "ms",
            )
            self.assertIn("<svg", grouped.read_text(encoding="utf-8"))
            self.assertIn("Qualidade", grouped.read_text(encoding="utf-8"))
            self.assertIn("<svg", bars.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
