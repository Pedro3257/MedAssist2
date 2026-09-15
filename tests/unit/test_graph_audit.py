"""
Valida a transformação do estado final em registro de auditoria.

Os testes usam relógio e repositório falsos, sem acessar PostgreSQL.
"""

import unittest
from uuid import uuid4

from medassist.application.audit import AuditRecord
from medassist.application.graph_nodes import create_audit_node


class FakeAuditRepository:
    """Captura o registro que seria enviado ao PostgreSQL."""

    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def save(self, record: AuditRecord) -> int:
        """Armazena o registro em memória e retorna um ID fixo."""
        self.records.append(record)
        return 42


class GraphAuditTests(unittest.TestCase):
    def test_persists_final_graph_state(self) -> None:
        """Persiste decisão, correlation ID, latência e eventos."""
        repository = FakeAuditRepository()
        node = create_audit_node(
            repository,
            provider_name="ollama",
            configured_model="medassist-local:1.0.0",
            clock=lambda: 12.5,
        )
        correlation_id = str(uuid4())

        result = node(
            {
                "correlation_id": correlation_id,
                "started_at_monotonic": 10.0,
                "patient_id": "PAT-001",
                "question": "What is anemia?",
                "route": "blocked",
                "requires_human_validation": True,
                "audit_events": [
                    {
                        "node": "safety",
                        "outcome": "blocked",
                        "detail": "Blocked request.",
                    }
                ],
            }
        )

        self.assertEqual(result["audit_event_id"], 42)
        self.assertEqual(result["latency_ms"], 2500.0)
        self.assertEqual(len(repository.records), 1)

        record = repository.records[0]

        self.assertEqual(
            record.correlation_id,
            correlation_id,
        )
        self.assertEqual(record.decision, "blocked")
        self.assertEqual(record.provider, "ollama")
        self.assertEqual(
            record.model,
            "medassist-local:1.0.0",
        )
        self.assertEqual(len(record.graph_events), 2)

    def test_invalid_patient_id_is_not_persisted(
        self,
    ) -> None:
        """Remove identificador inválido para respeitar o banco."""
        repository = FakeAuditRepository()
        node = create_audit_node(
            repository,
            clock=lambda: 1.0,
        )

        node(
            {
                "correlation_id": str(uuid4()),
                "started_at_monotonic": 0.5,
                "patient_id": "INVALID",
                "question": "What is anemia?",
                "route": "blocked",
                "audit_events": [],
            }
        )

        self.assertIsNone(
            repository.records[0].patient_id
        )

    def test_works_without_persistence_repository(
        self,
    ) -> None:
        """Mantém auditoria em memória quando não há repositório."""
        node = create_audit_node(
            clock=lambda: 2.0,
        )

        result = node(
            {
                "correlation_id": str(uuid4()),
                "started_at_monotonic": 1.0,
                "patient_id": "PAT-001",
                "question": "What is anemia?",
                "route": "human_validation",
                "audit_events": [],
            }
        )

        self.assertNotIn("audit_event_id", result)
        self.assertEqual(result["latency_ms"], 1000.0)
        self.assertEqual(
            result["audit_events"][0]["node"],
            "audit",
        )

    def test_redacts_secrets_before_persistence(self) -> None:
        """Impede que credenciais coladas na entrada cheguem ao banco."""
        repository = FakeAuditRepository()
        node = create_audit_node(repository, clock=lambda: 1.0)
        google_key = "AIza" + "A" * 35
        bearer_token = "Bearer very-sensitive-token-value"

        node(
            {
                "correlation_id": str(uuid4()),
                "started_at_monotonic": 0.5,
                "patient_id": "PAT-001",
                "question": f"What is anemia? api_key={google_key}",
                "route": "provider_error",
                "error": f"Authorization: {bearer_token}",
                "audit_events": [
                    {
                        "node": "generation",
                        "outcome": "provider_error",
                        "detail": "password=my-secret-password",
                    }
                ],
            }
        )

        persisted = repr(repository.records[0])
        self.assertNotIn(google_key, persisted)
        self.assertNotIn("very-sensitive-token-value", persisted)
        self.assertNotIn("my-secret-password", persisted)
        self.assertIn("[REDACTED]", persisted)


if __name__ == "__main__":
    unittest.main()