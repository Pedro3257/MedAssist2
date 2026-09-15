import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = (ROOT / 'migrations' / '001_structured_data.sql').read_text(
    encoding='utf-8'
)
SEED = (ROOT / 'migrations' / '002_seed_synthetic_data.sql').read_text(
    encoding='utf-8'
)
# Carrega a migration de auditoria para validar sua estrutura.
AUDIT_SCHEMA = (
    ROOT / "migrations" / "006_audit_events.sql"
).read_text(encoding="utf-8")
COMPOSE = (ROOT / 'compose.yaml').read_text(encoding='utf-8')


def insert_block(table: str) -> str:
    match = re.search(
        rf'INSERT INTO {table}\b.*?VALUES\s*(.*?);\s*\n\s*\n',
        SEED,
        flags=re.DOTALL,
    )
    if not match:
        raise AssertionError(f'Insert for {table} not found')
    return match.group(1)


class DatabaseAssetTests(unittest.TestCase):
    def test_schema_has_relations_and_synthetic_guards(self) -> None:
        for table in ('patients', 'encounters', 'exams', 'pending_exams'):
            self.assertIn(f'CREATE TABLE {table}', SCHEMA)
        self.assertGreaterEqual(SCHEMA.count('CHECK (synthetic)'), 4)
        self.assertIn('REFERENCES patients(patient_id)', SCHEMA)
        self.assertIn('REFERENCES encounters(encounter_id)', SCHEMA)

    def test_seed_has_expected_synthetic_records(self) -> None:
        patients = set(re.findall(r'PAT-[0-9]{3}', insert_block('patients')))
        encounters = set(re.findall(r'ENC-[0-9]{3}', insert_block('encounters')))
        exams = set(re.findall(r'EXM-[0-9]{3}', insert_block('exams')))
        pending = set(re.findall(r'PEX-[0-9]{3}', insert_block('pending_exams')))
        self.assertEqual(len(patients), 12)
        self.assertEqual(len(encounters), 12)
        self.assertEqual(len(exams), 24)
        self.assertEqual(len(pending), 12)
        self.assertEqual(SEED.count('Paciente Sintetico '), 12)

    def test_all_patient_references_exist(self) -> None:
        patients = set(re.findall(r'PAT-[0-9]{3}', insert_block('patients')))
        for table in ('encounters', 'exams', 'pending_exams'):
            references = set(re.findall(r'PAT-[0-9]{3}', insert_block(table)))
            self.assertTrue(references <= patients)

    def test_compose_requires_password_and_runs_migrations(self) -> None:
        self.assertIn('pgvector/pgvector:pg16', COMPOSE)
        self.assertIn('POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?', COMPOSE)
        self.assertIn('./migrations:/docker-entrypoint-initdb.d:ro', COMPOSE)
        self.assertIn('pg_isready', COMPOSE)

    def test_audit_schema_has_required_fields(self) -> None:
        """Confirma os campos mínimos exigidos para rastreabilidade."""
        required_fields = (
            "correlation_id uuid NOT NULL UNIQUE",
            "question text NOT NULL",
            "decision varchar(40) NOT NULL",
            "provider varchar(50)",
            "model varchar(150)",
            "sources jsonb NOT NULL",
            "latency_ms numeric(12, 3)",
            "requires_human_validation boolean NOT NULL",
            "graph_events jsonb NOT NULL",
            "created_at timestamptz NOT NULL",
        )

        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, AUDIT_SCHEMA)

    def test_audit_schema_restricts_decisions_and_json(
        self,
    ) -> None:
        """Confirma decisões permitidas e arrays JSON válidos."""
        expected_decisions = (
            "blocked",
            "urgent",
            "patient_not_found",
            "insufficient_context",
            "human_validation",
            "provider_error",
            "completed",
        )

        for decision in expected_decisions:
            with self.subTest(decision=decision):
                self.assertIn(
                    f"'{decision}'",
                    AUDIT_SCHEMA,
                )

        self.assertGreaterEqual(
            AUDIT_SCHEMA.count(
                "jsonb_typeof("
            ),
            2,
        )
        self.assertIn(
            "CHECK (synthetic)",
            AUDIT_SCHEMA,
        )

    def test_audit_schema_has_query_indexes(self) -> None:
        """Confirma índices para data, decisão e paciente."""
        expected_indexes = (
            "idx_audit_events_created_at",
            "idx_audit_events_decision",
            "idx_audit_events_patient",
        )

        for index in expected_indexes:
            with self.subTest(index=index):
                self.assertIn(index, AUDIT_SCHEMA)

if __name__ == '__main__':
    unittest.main()
