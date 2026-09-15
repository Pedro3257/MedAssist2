"""
Valida a minimização do contexto enviado a providers remotos.

Os testes confirmam que identificadores e datas exatas são removidos,
preservando informações clínicas necessárias.
"""

import unittest
from datetime import date, datetime, timezone

from medassist.application.context_builder import GenerationContext
from medassist.application.patient_context import (
    Encounter,
    Exam,
    Patient,
    PatientContext,
    PendingExam,
)
from medassist.application.privacy import (
    minimize_generation_context,
)


def create_patient_context() -> PatientContext:
    """Cria um prontuário sintético completo para os testes."""
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


class PrivacyTests(unittest.TestCase):
    def test_removes_direct_identifiers_and_dates(self) -> None:
        """Remove nome, nascimento, IDs e datas exatas."""
        patient_context = create_patient_context()
        generation_context = GenerationContext(
            patient_id="PAT-001",
            patient_text="Full patient context.",
            evidence_text="Medical evidence.",
            sources=(),
        )

        minimized = minimize_generation_context(
            generation_context,
            patient_context,
        )

        forbidden_values = (
            "PAT-001",
            "Paciente Sintético 001",
            "1980-05-14",
            "ENC-001",
            "EXM-001",
            "PEX-001",
            "2026-08-20",
        )

        for value in forbidden_values:
            with self.subTest(value=value):
                self.assertNotIn(
                    value,
                    minimized.patient_text,
                )

    def test_preserves_required_clinical_information(
        self,
    ) -> None:
        """Preserva sexo, sintomas, exames e status pendente."""
        patient_context = create_patient_context()
        generation_context = GenerationContext(
            patient_id="PAT-001",
            patient_text="Full patient context.",
            evidence_text="Medical evidence.",
            sources=(),
        )

        minimized = minimize_generation_context(
            generation_context,
            patient_context,
        )

        required_values = (
            "female",
            "Fadiga persistente",
            "Cansaço há duas semanas",
            "Hemograma",
            "Hemoglobina 11,2 g/dL",
            "Ferritina",
            "scheduled",
        )

        for value in required_values:
            with self.subTest(value=value):
                self.assertIn(
                    value,
                    minimized.patient_text,
                )

    def test_preserves_internal_provenance(self) -> None:
        """Mantém patient_id e evidências fora do texto minimizado."""
        patient_context = create_patient_context()
        generation_context = GenerationContext(
            patient_id="PAT-001",
            patient_text="Full patient context.",
            evidence_text="Medical evidence.",
            sources=(),
        )

        minimized = minimize_generation_context(
            generation_context,
            patient_context,
        )

        self.assertEqual(
            minimized.patient_id,
            "PAT-001",
        )
        self.assertEqual(
            minimized.evidence_text,
            "Medical evidence.",
        )

if __name__ == "__main__":
    unittest.main()