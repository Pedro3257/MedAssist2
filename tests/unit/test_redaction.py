"""
Valida a remoção de segredos antes de logs e registros de auditoria.

Os testes usam apenas credenciais fictícias e nunca exibem valores reais.
"""

import unittest

from medassist.application.redaction import (
    REDACTED,
    redact_audit_events,
    redact_secrets,
)


class RedactionTests(unittest.TestCase):
    def test_redacts_common_secret_formats(self) -> None:
        """Remove chave Google, Bearer token e senha atribuída."""
        google_key = "AIza" + "B" * 35
        original = (
            f"api_key={google_key} "
            "Bearer token-with-private-value "
            "password=private-password"
        )

        result = redact_secrets(original)

        self.assertNotIn(google_key, result)
        self.assertNotIn("token-with-private-value", result)
        self.assertNotIn("private-password", result)
        self.assertEqual(result.count(REDACTED), 3)

    def test_preserves_non_secret_clinical_text(self) -> None:
        """Mantém conteúdo clínico comum que não contém credenciais."""
        text = "Paciente sintético relata fadiga persistente."
        self.assertEqual(redact_secrets(text), text)

    def test_redacts_event_details_without_mutating_source(self) -> None:
        """Cria cópia segura do evento e preserva o objeto original."""
        events = (
            {
                "node": "generation",
                "detail": "token=private-token-value",
            },
        )

        result = redact_audit_events(events)

        self.assertEqual(result[0]["detail"], REDACTED)
        self.assertEqual(
            events[0]["detail"],
            "token=private-token-value",
        )


if __name__ == "__main__":
    unittest.main()