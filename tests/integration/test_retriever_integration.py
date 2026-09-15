"""Valida recuperação multilíngue e abstenção com Ollama e PostgreSQL reais."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from medassist.infrastructure.config import load_env_file
from medassist.infrastructure.pgvector_retriever import (
    OllamaEmbeddingProvider,
    PgVectorRetriever,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(
    os.getenv("RUN_RAG_INTEGRATION") == "1",
    "Defina RUN_RAG_INTEGRATION=1 para usar Ollama e PostgreSQL reais.",
)
class RetrieverIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Abre uma única conexão real para os três cenários do teste."""
        import psycopg

        load_env_file(PROJECT_ROOT / ".env")
        cls.connection = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "medassist"),
            user=os.getenv("POSTGRES_USER", "medassist"),
            password=os.environ["POSTGRES_PASSWORD"],
        )
        cls.retriever = PgVectorRetriever(
            cls.connection,
            OllamaEmbeddingProvider(
                model=os.getenv(
                    "OLLAMA_EMBEDDING_MODEL",
                    "embeddinggemma:300m",
                ),
                base_url=os.getenv(
                    "OLLAMA_BASE_URL",
                    "http://127.0.0.1:11434",
                ),
            ),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        """Fecha a conexão real após todos os cenários."""
        cls.connection.close()

    def assert_kidney_stone_result(self, query: str) -> None:
        """Confirma que o primeiro resultado trata de cálculos renais."""
        response = self.retriever.search(
            query,
            limit=5,
            minimum_similarity=0.55,
        )

        self.assertFalse(response.abstained)
        self.assertGreaterEqual(response.results[0].similarity, 0.55)
        self.assertIn("kidney stone", response.results[0].content.lower())
        self.assertTrue(response.results[0].collection)
        self.assertTrue(response.results[0].source)
        self.assertTrue(response.results[0].url)

    def test_retrieves_english_medical_question(self) -> None:
        self.assert_kidney_stone_result(
            "What are the treatments for kidney stones?"
        )

    def test_retrieves_portuguese_medical_question(self) -> None:
        self.assert_kidney_stone_result(
            "Como são tratadas as pedras nos rins?"
        )

    def test_abstains_for_unrelated_question(self) -> None:
        response = self.retriever.search(
            "Como configurar uma rede Wi-Fi doméstica?",
            limit=5,
            minimum_similarity=0.55,
        )

        self.assertTrue(response.abstained)


if __name__ == "__main__":
    unittest.main()
