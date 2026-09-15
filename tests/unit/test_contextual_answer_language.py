"""Testa a revisão controlada quando o modelo responde no idioma incorreto."""

from __future__ import annotations

import unittest

from medassist.application.context_builder import GenerationContext, SourceReference
from medassist.application.contextual_answer import ContextualAnswerService
from medassist.application.llm import LLMRequest, LLMResponse


class SequentialProvider:
    """Retorna primeiro inglês e depois uma revisão em português."""

    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        content = (
            "Kidney stone treatment depends on stone size."
            if len(self.requests) == 1
            else "O tratamento das pedras nos rins depende do tamanho do cálculo."
        )
        return LLMResponse(
            content=content,
            provider="fake",
            model=request.model,
            latency_ms=1.0,
        )


class ContextualAnswerLanguageTests(unittest.TestCase):
    def test_rewrites_once_when_answer_language_is_incorrect(self) -> None:
        provider = SequentialProvider()
        source = SourceReference(
            position=1,
            collection="NIDDK",
            source="NIDDK",
            url="https://example.test/kidney-stones",
            chunk_id="chunk-001",
            similarity=0.75,
        )
        context = GenerationContext(
            patient_id="PAT-001",
            patient_text="Synthetic patient data",
            evidence_text="[Evidence 1] Kidney stone evidence",
            sources=(source,),
        )

        answer = ContextualAnswerService(provider).generate(
            question="Como são tratadas as pedras nos rins?",
            context=context,
            model="fake-model",
            language_rewrite_model="translator-model",
        )

        self.assertEqual(len(provider.requests), 2)
        self.assertTrue(answer.language_rewrite_performed)
        self.assertEqual(provider.requests[1].model, "translator-model")
        self.assertEqual(answer.model, "fake-model")
        self.assertEqual(answer.rewrite_model, "translator-model")
        self.assertIn("Kidney stone", answer.initial_model_content or "")
        self.assertIn("tratamento", answer.answer_text.casefold())
        self.assertIn(
            "Required response language: Brazilian Portuguese",
            provider.requests[1].user_prompt,
        )


if __name__ == "__main__":
    unittest.main()
