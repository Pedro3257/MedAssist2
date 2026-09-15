"""Testa os contratos e a consulta vetorial sem depender de Ollama ou banco reais."""

from __future__ import annotations

import unittest

from medassist.application.retrieval import RetrievedChunk, RetrievalResponse
from medassist.infrastructure.pgvector_retriever import PgVectorRetriever


class FakeEmbeddingProvider:
    """Fornece um embedding determinístico com a dimensão do projeto."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 768 for _ in texts]


class FakeCursor:
    """Simula somente as operações de cursor necessárias ao retriever."""

    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self.rows = rows
        self.statement = ""
        self.parameters: tuple[object, ...] = ()

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(
        self,
        statement: str,
        parameters: tuple[object, ...],
    ) -> None:
        self.statement = statement
        self.parameters = parameters

    def fetchall(self) -> list[tuple[object, ...]]:
        return self.rows


class FakeConnection:
    """Expõe um cursor falso para validar a montagem da consulta SQL."""

    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self.fake_cursor = FakeCursor(rows)

    def cursor(self) -> FakeCursor:
        return self.fake_cursor


class RetrievalTests(unittest.TestCase):
    def test_maps_result_with_similarity_and_provenance(self) -> None:
        connection = FakeConnection(
            [
                (
                    "chunk-001",
                    "document-001",
                    "Question: Kidney stones?\nAnswer: Treatment...",
                    0.6434,
                    "5_NIDDK_QA",
                    "NIDDK",
                    "https://example.test/kidney-stones",
                )
            ]
        )

        response = PgVectorRetriever(
            connection,
            FakeEmbeddingProvider(),
        ).search(
            "Como são tratadas as pedras nos rins?",
            limit=3,
            minimum_similarity=0.55,
        )

        self.assertFalse(response.abstained)
        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.results[0].source, "NIDDK")
        self.assertEqual(response.results[0].collection, "5_NIDDK_QA")
        self.assertAlmostEqual(response.results[0].similarity, 0.6434)
        self.assertIn("vector", connection.fake_cursor.statement)
        self.assertEqual(connection.fake_cursor.parameters[1:], (0.55, 3))

    def test_abstains_when_database_returns_no_evidence(self) -> None:
        response = PgVectorRetriever(
            FakeConnection([]),
            FakeEmbeddingProvider(),
        ).search(
            "Como configurar uma rede Wi-Fi doméstica?",
            minimum_similarity=0.55,
        )

        self.assertTrue(response.abstained)
        self.assertEqual(response.results, ())

    def test_rejects_invalid_search_arguments(self) -> None:
        retriever = PgVectorRetriever(
            FakeConnection([]),
            FakeEmbeddingProvider(),
        )

        with self.assertRaises(ValueError):
            retriever.search("   ")
        with self.assertRaises(ValueError):
            retriever.search("question", limit=0)
        with self.assertRaises(ValueError):
            retriever.search("question", minimum_similarity=1.1)

    def test_retrieval_response_and_chunk_validate_domain_data(self) -> None:
        result = RetrievedChunk(
            chunk_id="chunk-001",
            document_id="document-001",
            content="Medical evidence",
            similarity=0.75,
            collection="collection",
            source="source",
            url="https://example.test",
        )
        response = RetrievalResponse(
            query="question",
            results=(result,),
            minimum_similarity=0.55,
        )

        self.assertFalse(response.abstained)
        with self.assertRaises(ValueError):
            RetrievedChunk(
                chunk_id="chunk-002",
                document_id="document-002",
                content="evidence",
                similarity=1.1,
                collection="collection",
                source=None,
                url=None,
            )


if __name__ == "__main__":
    unittest.main()

