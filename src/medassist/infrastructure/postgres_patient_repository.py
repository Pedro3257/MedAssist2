"""Consulta o contexto estruturado de pacientes sintéticos no PostgreSQL."""

from __future__ import annotations

import re
from typing import Any

import psycopg

from medassist.application.patient_context import (
    Encounter,
    Exam,
    Patient,
    PatientContext,
    PendingExam,
)


PATIENT_ID_PATTERN = re.compile(r"^PAT-[0-9]{3}$")


class PostgresPatientRepository:
    """Recupera cadastro, atendimentos e exames de um único paciente."""

    def __init__(
        self,
        connection: psycopg.Connection[Any],
    ) -> None:
        self.connection = connection

    def get_by_id(
        self,
        patient_id: str,
    ) -> PatientContext | None:
        """Retorna o contexto completo ou None quando o paciente não existe."""
        patient_id = patient_id.strip().upper()

        if not PATIENT_ID_PATTERN.fullmatch(patient_id):
            raise ValueError(
                "patient_id deve seguir o formato PAT-000"
            )

        with self.connection.cursor() as cursor:
            patient = self._load_patient(cursor, patient_id)

            if patient is None:
                return None

            encounters = self._load_encounters(
                cursor,
                patient_id,
            )
            exams = self._load_exams(
                cursor,
                patient_id,
            )
            pending_exams = self._load_pending_exams(
                cursor,
                patient_id,
            )

        return PatientContext(
            patient=patient,
            encounters=encounters,
            exams=exams,
            pending_exams=pending_exams,
        )

    @staticmethod
    def _load_patient(
        cursor: Any,
        patient_id: str,
    ) -> Patient | None:
        """Consulta somente o cadastro do paciente solicitado."""
        cursor.execute(
            """
            SELECT
                patient_id,
                display_name,
                birth_date,
                biological_sex,
                synthetic
            FROM patients
            WHERE patient_id = %s
            """,
            (patient_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return Patient(
            patient_id=row[0],
            display_name=row[1],
            birth_date=row[2],
            biological_sex=row[3],
            synthetic=row[4],
        )

    @staticmethod
    def _load_encounters(
        cursor: Any,
        patient_id: str,
    ) -> tuple[Encounter, ...]:
        """Consulta os atendimentos do paciente em ordem cronológica inversa."""
        cursor.execute(
            """
            SELECT
                encounter_id,
                occurred_at,
                reason,
                clinical_notes
            FROM encounters
            WHERE patient_id = %s
            ORDER BY occurred_at DESC
            """,
            (patient_id,),
        )

        return tuple(
            Encounter(
                encounter_id=row[0],
                occurred_at=row[1],
                reason=row[2],
                clinical_notes=row[3],
            )
            for row in cursor.fetchall()
        )

    @staticmethod
    def _load_exams(
        cursor: Any,
        patient_id: str,
    ) -> tuple[Exam, ...]:
        """Consulta somente os exames concluídos do paciente."""
        cursor.execute(
            """
            SELECT
                exam_id,
                encounter_id,
                exam_type,
                collected_at,
                result_text,
                reference_text,
                status
            FROM exams
            WHERE patient_id = %s
              AND status = 'completed'
            ORDER BY collected_at DESC
            """,
            (patient_id,),
        )

        return tuple(
            Exam(
                exam_id=row[0],
                encounter_id=row[1],
                exam_type=row[2],
                collected_at=row[3],
                result_text=row[4],
                reference_text=row[5],
                status=row[6],
            )
            for row in cursor.fetchall()
        )

    @staticmethod
    def _load_pending_exams(
        cursor: Any,
        patient_id: str,
    ) -> tuple[PendingExam, ...]:
        """Consulta exames pendentes e agendados, excluindo cancelados."""
        cursor.execute(
            """
            SELECT
                pending_exam_id,
                encounter_id,
                exam_type,
                requested_at,
                scheduled_for,
                status
            FROM pending_exams
            WHERE patient_id = %s
              AND status IN ('pending', 'scheduled')
            ORDER BY requested_at DESC
            """,
            (patient_id,),
        )

        return tuple(
            PendingExam(
                pending_exam_id=row[0],
                encounter_id=row[1],
                exam_type=row[2],
                requested_at=row[3],
                scheduled_for=row[4],
                status=row[5],
            )
            for row in cursor.fetchall()
        )