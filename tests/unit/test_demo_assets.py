"""Valida o roteiro, as perguntas e o executor da demonstração."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from medassist.application.safety import evaluate_request


ROOT = Path(__file__).resolve().parents[2]


class DemoAssetsTests(unittest.TestCase):
    """Confirma que os casos oficiais são estáveis e seguros para apresentação."""

    def setUp(self) -> None:
        """Carrega as perguntas oficiais antes de cada validação."""
        self.cases = json.loads(
            (ROOT / "configs" / "demo_questions.json").read_text(encoding="utf-8")
        )

    def test_has_unique_cases_and_expected_routes(self) -> None:
        """Exige quatro identificadores e somente rotas demonstráveis."""
        self.assertEqual(len(self.cases), 4)
        self.assertEqual(len({case["id"] for case in self.cases}), 4)
        self.assertTrue(
            {case["expected_route"] for case in self.cases}
            <= {"human_validation", "blocked"}
        )

    def test_blocked_cases_match_safety_policy(self) -> None:
        """Evita que mudanças nas perguntas eliminem os bloqueios esperados."""
        blocked = [case for case in self.cases if case["expected_route"] == "blocked"]
        self.assertEqual(len(blocked), 2)
        for case in blocked:
            with self.subTest(case=case["id"]):
                self.assertFalse(evaluate_request(case["question"]).allowed)

    def test_runner_checks_routes_and_saves_transcript(self) -> None:
        """Confirma as proteções mínimas do executor PowerShell."""
        runner = (ROOT / "scripts" / "run_demo.ps1").read_text(encoding="utf-8")
        self.assertIn("expected_route", runner)
        self.assertIn("Write-DemoTranscript", runner)
        self.assertIn("[System.IO.File]::AppendAllLines", runner)
        self.assertIn("[System.Text.UTF8Encoding]::new($false)", runner)
        self.assertIn("yyyyMMdd-HHmmssfff", runner)
        self.assertIn('(\"PERGUNTA: \" + $case.question)', runner)
        self.assertIn("reports\\evidence\\demo", runner)


if __name__ == "__main__":
    unittest.main()