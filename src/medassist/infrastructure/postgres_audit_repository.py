"""
Persiste registros de auditoria do MedAssist no PostgreSQL.

O repositório utiliza parâmetros SQL e Jsonb, evitando concatenação de
valores e mantendo fontes e eventos como arrays JSON estruturados.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from medassist.application.audit import AuditRecord


class PostgresAuditRepository:
    """Grava uma execução completa na tabela audit_events."""

    def __init__(
        self,
        connection: psycopg.Connection[Any],
    ) -> None:
        self.connection = connection

    def save(
        self,
        record: AuditRecord,
    ) -> int:
        """Persiste o registro e retorna o audit_event_id."""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit_events (
                    correlation_id,
                    patient_id,
                    question,
                    decision,
                    provider,
                    model,
                    sources,
                    latency_ms,
                    requires_human_validation,
                    error_code,
                    graph_events,
                    synthetic
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    true
                )
                RETURNING audit_event_id
                """,
                (
                    record.correlation_id,
                    record.patient_id,
                    record.question,
                    record.decision,
                    record.provider,
                    record.model,
                    Jsonb(list(record.sources)),
                    record.latency_ms,
                    record.requires_human_validation,
                    record.error_code,
                    Jsonb(list(record.graph_events)),
                ),
            )

            row = cursor.fetchone()

        if row is None:
            raise RuntimeError(
                "O PostgreSQL não retornou audit_event_id"
            )

        return int(row[0])