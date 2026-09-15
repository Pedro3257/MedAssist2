"""
Valida estrutura, proveniência e segurança das respostas.

Os testes não executam provider, banco de dados ou recuperação vetorial.
"""

import unittest
from dataclasses import replace

from medassist.application.answer_validation import (
    validate_contextual_answer,
)
from medassist.application.context_builder import SourceReference
from medassist.application.contextual_answer import ContextualAnswer


def create_source() -> SourceReference:
    """Cria uma fonte válida e rastreável."""
    return SourceReference(
        position=1,
        collection="test_collection",
        source="Test Source",
        url="https://example.test/evidence",
        chunk_id="chunk-001",
        similarity=0.75,
    )


def create_valid_answer() -> ContextualAnswer:
    """Cria uma resposta válida produzida por LLM."""
    return ContextualAnswer(
        answer_text="Educational medical information.",
        patient_id="PAT-001",
        sources=(create_source(),),
        limitations="General information only.",
        human_validation="Professional validation required.",
        provider="fake",
        model="fake-model",
        used_llm=True,
    )


class AnswerValidationTests(unittest.TestCase):
    def test_accepts_grounded_answer(self) -> None:
        """Aceita resposta com paciente e fonte válidos."""
        result = validate_contextual_answer(
            create_valid_answer(),
            expected_patient_id="PAT-001",
        )

        self.assertTrue(result.valid)
        self.assertIsNone(result.reason)

    def test_accepts_fallback_without_sources(self) -> None:
        """Aceita abstenção determinística sem fontes."""
        answer = ContextualAnswer(
            answer_text="Insufficient evidence.",
            patient_id="PAT-001",
            sources=(),
            limitations="General information only.",
            human_validation="Professional validation required.",
            provider="fallback",
            model="none",
            used_llm=False,
        )

        result = validate_contextual_answer(
            answer,
            expected_patient_id="PAT-001",
        )

        self.assertTrue(result.valid)

    def test_rejects_wrong_patient(self) -> None:
        """Impede que uma resposta seja associada a outro paciente."""
        answer = replace(
            create_valid_answer(),
            patient_id="PAT-999",
        )

        result = validate_contextual_answer(
            answer,
            expected_patient_id="PAT-001",
        )

        self.assertFalse(result.valid)
        self.assertIn("outro paciente", result.reason)

    def test_rejects_generated_answer_without_sources(self) -> None:
        """Exige proveniência quando a LLM foi executada."""
        answer = replace(
            create_valid_answer(),
            sources=(),
        )

        result = validate_contextual_answer(
            answer,
            expected_patient_id="PAT-001",
        )

        self.assertFalse(result.valid)
        self.assertIn("fontes", result.reason)

    def test_rejects_invalid_source_url(self) -> None:
        """Exige URL HTTP ou HTTPS para cada fonte."""
        invalid_source = replace(
            create_source(),
            url="invalid-url",
        )
        answer = replace(
            create_valid_answer(),
            sources=(invalid_source,),
        )

        result = validate_contextual_answer(
            answer,
            expected_patient_id="PAT-001",
        )

        self.assertFalse(result.valid)
        self.assertIn("URL", result.reason)

    def test_blocks_explicit_dosage_in_output(self) -> None:
        """Bloqueia uma dosagem produzida indevidamente pela LLM."""
        answer = replace(
            create_valid_answer(),
            answer_text="Tome 500 mg do medicamento.",
        )

        result = validate_contextual_answer(
            answer,
            expected_patient_id="PAT-001",
        )

        self.assertFalse(result.valid)
        self.assertTrue(result.safety_violation)
        self.assertIn("dosagem", result.reason)