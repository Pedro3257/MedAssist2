"""
Valida o repositório de auditoria sem acessar PostgreSQL real.

O teste confirma SQL parametrizado, JSON estruturado e retorno do ID.
"""

import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from psycopg.types.json import Jsonb

from medassist.application.audit import AuditRecord
from medassist.infrastructure.postgres_audit_repository import (
    PostgresAuditRepository,
)


class PostgresAuditRepositoryTests(unittest.TestCase):
    def test_saves_parameterized_audit_record(self) -> None:
        """Persiste parâmetros sem concatenar valores ao SQL."""
        cursor = MagicMock()
        cursor.fetchone.return_value = (42,)

        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = (
            cursor
        )

        repository = PostgresAuditRepository(connection)

        secret_marker = "must-not-appear-in-sql"

        record = AuditRecord(
            correlation_id=str(uuid4()),
            patient_id="PAT-001",
            question=(
                "What is anemia? "
                f"{secret_marker}"
            ),
            decision="human_validation",
            provider="fake",
            model="fake-model",
            sources=(
                {
                    "position": 1,
                    "source": "Test Source",
                    "url": "https://example.test/evidence",
                },
            ),
            latency_ms=25.5,
            requires_human_validation=True,
            error_code=None,
            graph_events=(
                {
                    "node": "audit",
                    "outcome": "human_validation",
                    "detail": "Execution completed.",
                },
            ),
        )

        audit_event_id = repository.save(record)

        self.assertEqual(audit_event_id, 42)

        sql, parameters = cursor.execute.call_args.args

        self.assertIn(
            "INSERT INTO audit_events",
            sql,
        )
        self.assertNotIn(
            secret_marker,
            sql,
        )
        self.assertEqual(
            parameters[0],
            record.correlation_id,
        )
        self.assertEqual(
            parameters[2],
            record.question,
        )
        self.assertIsInstance(
            parameters[6],
            Jsonb,
        )
        self.assertIsInstance(
            parameters[10],
            Jsonb,
        )
        connection.commit.assert_not_called()

if __name__ == "__main__":
    unittest.main()