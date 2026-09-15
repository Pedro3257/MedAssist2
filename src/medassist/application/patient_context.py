"""Define os dados estruturados de paciente usados no contexto do MedAssist."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class Patient:
    """Representa somente os dados necessários do paciente sintético."""

    patient_id: str
    display_name: str
    birth_date: date
    biological_sex: str
    synthetic: bool


@dataclass(frozen=True, slots=True)
class Encounter:
    """Representa um atendimento pertencente ao paciente consultado."""

    encounter_id: str
    occurred_at: datetime
    reason: str
    clinical_notes: str


@dataclass(frozen=True, slots=True)
class Exam:
    """Representa o resultado de um exame concluído."""

    exam_id: str
    encounter_id: str | None
    exam_type: str
    collected_at: datetime
    result_text: str
    reference_text: str | None
    status: str


@dataclass(frozen=True, slots=True)
class PendingExam:
    """Representa um exame pendente ou agendado."""

    pending_exam_id: str
    encounter_id: str | None
    exam_type: str
    requested_at: datetime
    scheduled_for: datetime | None
    status: str


@dataclass(frozen=True, slots=True)
class PatientContext:
    """Agrupa todos os dados estruturados do paciente consultado."""

    patient: Patient
    encounters: tuple[Encounter, ...]
    exams: tuple[Exam, ...]
    pending_exams: tuple[PendingExam, ...]

    def __post_init__(self) -> None:
        patient_id = self.patient.patient_id

        if not patient_id.strip():
            raise ValueError("patient_id não pode estar vazio")

        if not self.patient.synthetic:
            raise ValueError(
                "O MVP aceita somente pacientes sintéticos"
            )

    @property
    def has_pending_exams(self) -> bool:
        """Indica se existem exames pendentes ou agendados."""
        return bool(self.pending_exams)