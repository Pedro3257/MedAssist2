"""
Confirma os dados efetivamente enviados ao provider remoto.

O teste percorre o LangGraph com um provider capturador e verifica que
nome, nascimento, IDs e datas não aparecem no prompt enviado à LLM.
"""

import unittest
from datetime import date, datetime, timezone

from langchain_core.documents import Document

from medassist.application.contextual_answer import (
    ContextualAnswerService,
)
from medassist.application.graph_workflow import (
    build_medassist_graph,
)
from medassist.application.llm import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
)
from medassist.application.patient_context import (
    Encounter,
    Exam,
    Patient,
    PatientContext,
    PendingExam,
)


class FakePatientRepository:
    """Fornece um prontuário sintético completo ao grafo."""

    def __init__(
        self,
        patient_context: PatientContext,
    ) -> None:
        self.patient_context = patient_context

    def get_by_id(
        self,
        patient_id: str,
    ) -> PatientContext | None:
        """Retorna o paciente usado na validação."""
        return self.patient_context


class FakeRetriever:
    """Fornece uma evidência pública rastreável."""

    def invoke(
        self,
        input: str,
    ) -> list[Document]:
        """Retorna uma evidência sem executar embeddings."""
        return [
            Document(
                page_content=(
                    "Anemia is a condition involving "
                    "red blood cells."
                ),
                metadata={
                    "similarity": 0.80,
                    "collection": "test_collection",
                    "source": "Test Source",
                    "url": "https://example.test/anemia",
                    "chunk_id": "chunk-001",
                },
            )
        ]


class CapturingProvider(LLMProvider):
    """Captura as requisições que seriam enviadas à API remota."""

    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    @property
    def name(self) -> str:
        """Identifica o provider falso como remoto."""
        return "google_ai"

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """Registra o prompt e devolve uma resposta segura."""
        self.requests.append(request)

        return LLMResponse(
            content=(
                "Anemia is a condition involving red blood cells, "
                "according to the provided educational evidence."
            ),
            provider=self.name,
            model=request.model,
            latency_ms=5.0,
            input_tokens=100,
            output_tokens=20,
            finish_reason="STOP",
        )


def create_patient_context() -> PatientContext:
    """Cria dados sintéticos com identificadores detectáveis."""
    occurred_at = datetime(
        2026,
        8,
        20,
        12,
        0,
        tzinfo=timezone.utc,
    )

    return PatientContext(
        patient=Patient(
            patient_id="PAT-001",
            display_name="Paciente Sintético 001",
            birth_date=date(1980, 5, 14),
            biological_sex="female",
            synthetic=True,
        ),
        encounters=(
            Encounter(
                encounter_id="ENC-001",
                occurred_at=occurred_at,
                reason="Fadiga persistente",
                clinical_notes="Cansaço há duas semanas.",
            ),
        ),
        exams=(
            Exam(
                exam_id="EXM-001",
                encounter_id="ENC-001",
                exam_type="Hemograma",
                collected_at=occurred_at,
                result_text="Hemoglobina 11,2 g/dL",
                reference_text="Referência sintética.",
                status="completed",
            ),
        ),
        pending_exams=(
            PendingExam(
                pending_exam_id="PEX-001",
                encounter_id="ENC-001",
                exam_type="Ferritina",
                requested_at=occurred_at,
                scheduled_for=occurred_at,
                status="scheduled",
            ),
        ),
    )


def invoke_graph(
    *,
    minimize_remote_context: bool,
) -> tuple[dict[str, object], CapturingProvider]:
    """Executa o grafo e devolve o resultado e o prompt capturado."""
    provider = CapturingProvider()

    graph = build_medassist_graph(
        repository=FakePatientRepository(
            create_patient_context()
        ),
        retriever=FakeRetriever(),
        answer_service=ContextualAnswerService(
            provider
        ),
        model="fake-google-model",
        provider_name=provider.name,
        minimize_remote_context=minimize_remote_context,
    )

    result = graph.invoke(
        {
            "patient_id": "PAT-001",
            "question": "What is anemia?",
            "audit_events": [],
        }
    )

    return result, provider


class RemoteContextFlowTests(unittest.TestCase):
    def test_remote_prompt_excludes_direct_identifiers(
        self,
    ) -> None:
        """Remove identificadores antes da chamada ao provider."""
        result, provider = invoke_graph(
            minimize_remote_context=True
        )

        self.assertEqual(
            result["route"],
            "human_validation",
        )
        self.assertEqual(len(provider.requests), 1)

        prompt = provider.requests[0].user_prompt

        forbidden_values = (
            "PAT-001",
            "Paciente Sintético 001",
            "1980-05-14",
            "ENC-001",
            "EXM-001",
            "PEX-001",
            "2026-08-20",
            "Referência sintética",
        )

        for value in forbidden_values:
            with self.subTest(value=value):
                self.assertNotIn(value, prompt)

    def test_remote_prompt_preserves_clinical_context(
        self,
    ) -> None:
        """Preserva dados clínicos necessários para contextualização."""
        _, provider = invoke_graph(
            minimize_remote_context=True
        )

        prompt = provider.requests[0].user_prompt

        required_values = (
            "female",
            "Fadiga persistente",
            "Cansaço há duas semanas",
            "Hemograma",
            "Hemoglobina 11,2 g/dL",
            "Ferritina",
            "scheduled",
            "Anemia is a condition",
            "https://example.test/anemia",
        )

        for value in required_values:
            with self.subTest(value=value):
                self.assertIn(value, prompt)

    def test_local_prompt_can_use_complete_synthetic_context(
        self,
    ) -> None:
        """Mantém o contexto completo quando a minimização está desligada."""
        _, provider = invoke_graph(
            minimize_remote_context=False
        )

        prompt = provider.requests[0].user_prompt

        self.assertIn("PAT-001", prompt)
        self.assertIn(
            "Paciente Sintético 001",
            prompt,
        )
        self.assertIn("1980-05-14", prompt)
        self.assertIn("ENC-001", prompt)

if __name__ == "__main__":
    unittest.main()