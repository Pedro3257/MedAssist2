"""Testa os cálculos da análise preliminar da avaliação comparativa."""

from __future__ import annotations

import unittest

from scripts.build_preliminary_evaluation_analysis import percentage_change


class PreliminaryEvaluationAnalysisTests(unittest.TestCase):
    """Valida cálculos usados nas comparações apresentadas no relatório."""

    def test_percentage_change_preserves_direction(self) -> None:
        """Distingue crescimento e redução em relação ao cenário inicial."""
        self.assertAlmostEqual(percentage_change(10.0, 15.0), 50.0)
        self.assertAlmostEqual(percentage_change(10.0, 4.0), -60.0)


if __name__ == "__main__":
    unittest.main()
