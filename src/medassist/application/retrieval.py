"""Define os contratos independentes de infraestrutura para recuperação RAG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """Representa um trecho médico recuperado com sua proveniência."""

    chunk_id: str
    document_id: str
    content: str
    similarity: float
    collection: str
    source: str | None
    url: str | None

    def __post_init__(self) -> None:
        if not self.chunk_id.strip():
            raise ValueError("chunk_id não pode estar vazio")
        if not self.document_id.strip():
            raise ValueError("document_id não pode estar vazio")
        if not self.content.strip():
            raise ValueError("content não pode estar vazio")
        if not 0.0 <= self.similarity <= 1.0:
            raise ValueError("similarity deve estar entre 0.0 e 1.0")
        if not self.collection.strip():
            raise ValueError("collection não pode estar vazia")


@dataclass(frozen=True, slots=True)
class RetrievalResponse:
    """Agrupa resultados e informa quando não há evidência suficiente."""

    query: str
    results: tuple[RetrievedChunk, ...]
    minimum_similarity: float

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("query não pode estar vazia")
        if not 0.0 <= self.minimum_similarity <= 1.0:
            raise ValueError("minimum_similarity deve estar entre 0.0 e 1.0")

    @property
    def abstained(self) -> bool:
        """Indica ausência de evidência acima do limiar configurado."""
        return not self.results


class EmbeddingProvider(Protocol):
    """Contrato mínimo de um gerador de embeddings."""

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Gera um vetor para cada texto recebido."""

