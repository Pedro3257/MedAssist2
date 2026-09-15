"""Testa a estrutura determinística e o fallback da resposta contextual."""

from __future__ import annotations

import unittest

from medassist.application.context_builder import GenerationContext, SourceReference
from medassist.application.contextual_answer import ContextualAnswerService
from medassist.application.llm import (
    LLMProviderInvalidResponseError,
    LLMRequest,
    LLMResponse,
)


class FakeProvider:
    """Simula um modelo que retorna somente a resposta principal."""

    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(
            content="ANSWER:\nGeneral medical answer from evidence.",
            provider="fake",
            model=request.model,
            latency_ms=1.0,
        )


def context_with_evidence() -> GenerationContext:
    """Cria um contexto mínimo com uma fonte rastreável."""
    source = SourceReference(
        position=1,
        collection="GARD",
        source="GARD",
        url="https://example.test/evidence",
        chunk_id="chunk-001",
        similarity=0.75,
    )
    return GenerationContext(
        patient_id="PAT-001",
        patient_text="Synthetic patient data",
        evidence_text="[Evidence 1] Medical evidence",
        sources=(source,),
    )


class ContextualAnswerServiceTests(unittest.TestCase):
    def test_builds_structure_when_model_returns_only_answer(self) -> None:
        provider = FakeProvider()
        answer = ContextualAnswerService(provider).generate(
            question="What is this condition?",
            context=context_with_evidence(),
            model="fake-model",
        )

        self.assertEqual(
            answer.answer_text,
            "General medical answer from evidence.",
        )
        self.assertIn("ANSWER:\n", answer.content)
        self.assertIn(
            "EVIDENCE RETRIEVED:\n[Evidence 1]",
            answer.content,
        )
        self.assertIn("SOURCES:\n[Evidence 1] GARD", answer.content)
        self.assertIn("LIMITATIONS:\n", answer.content)
        self.assertIn("HUMAN VALIDATION:\n", answer.content)
        self.assertEqual(len(provider.requests), 1)

    def test_fallback_does_not_call_model_without_evidence(self) -> None:
        provider = FakeProvider()
        context = GenerationContext(
            patient_id="PAT-001",
            patient_text="Synthetic patient data",
            evidence_text="No evidence",
            sources=(),
        )

        answer = ContextualAnswerService(provider).generate(
            question="O que pode ser concluído?",
            context=context,
            model="fake-model",
        )

        self.assertTrue(answer.abstained)
        self.assertFalse(answer.used_llm)
        self.assertEqual(provider.requests, [])
        self.assertIn("EVIDENCE RETRIEVED:\nNone", answer.content)
        self.assertIn("conclusão clínica", answer.limitations)

    def test_empty_main_answer_is_controlled_provider_error(self) -> None:
        """Classifica resposta composta apenas por seções como inválida."""
        class SectionsOnlyProvider(FakeProvider):
            def generate(self, request: LLMRequest) -> LLMResponse:
                return LLMResponse(
                    content="SOURCES:\n[Evidence 1]",
                    provider="fake",
                    model=request.model,
                    latency_ms=1.0,
                )

        with self.assertRaises(LLMProviderInvalidResponseError):
            ContextualAnswerService(SectionsOnlyProvider()).generate(
                question="What is this condition?",
                context=context_with_evidence(),
                model="fake-model",
            )


if __name__ == "__main__":
    unittest.main()