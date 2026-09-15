"""Valida os arquivos de configuração e inicialização reproduzível."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ProjectBootstrapTests(unittest.TestCase):
    """Confirma variáveis, dependências e proteções do inicializador."""

    def test_env_example_has_required_settings_without_secret(self) -> None:
        """Exige configurações e impede uma chave Google preenchida."""
        content = (ROOT / ".env.example").read_text(encoding="utf-8")
        required = {
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "LLM_PROVIDER",
            "OLLAMA_BASE_URL",
            "OLLAMA_MODEL",
            "OLLAMA_EMBEDDING_MODEL",
            "OLLAMA_EMBEDDING_TIMEOUT_SECONDS",
            "OLLAMA_LANGUAGE_REWRITE_MODEL",
            "GEMINI_API_KEY",
            "GOOGLE_AI_MODEL",
        }
        keys = {
            line.split("=", 1)[0]
            for line in content.splitlines()
            if line and not line.startswith("#") and "=" in line
        }
        self.assertTrue(required <= keys)
        self.assertIn("GEMINI_API_KEY=\n", content + "\n")
        self.assertNotIn("AIza", content)

    def test_runtime_requirements_are_exactly_pinned(self) -> None:
        """Evita dependências locais sem versão reproduzível."""
        lines = [
            line.strip()
            for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        self.assertTrue(lines)
        self.assertTrue(all("==" in line for line in lines))

    def test_bootstrap_has_safety_checks(self) -> None:
        """Confirma validação de segredo, saúde, modelos e base vetorial."""
        content = (ROOT / "scripts" / "start_medassist.ps1").read_text(encoding="utf-8")
        for expected in (
            "change-me-local-only",
            "docker compose config --quiet",
            "docker compose up -d postgres",
            "State.Health.Status",
            "OLLAMA_EMBEDDING_MODEL",
            "knowledge_chunks",
        ):
            self.assertIn(expected, content)


if __name__ == "__main__":
    unittest.main()