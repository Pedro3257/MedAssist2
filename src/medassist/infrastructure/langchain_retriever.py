"""Adapta o retriever pgvector do MedAssist à interface do LangChain."""

from __future__ import annotations

from langchain_core.callbacks import (
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict, Field

from medassist.infrastructure.pgvector_retriever import (
    PgVectorRetriever,
)


class LangChainPgVectorRetriever(BaseRetriever):
    """Expõe a busca pgvector como um retriever do LangChain."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    retriever: PgVectorRetriever

    limit: int = Field(
        default=5,
        gt=0,
    )

    minimum_similarity: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
    )

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        """Recupera evidências e as converte para documentos LangChain."""
        response = self.retriever.search(
            query,
            limit=self.limit,
            minimum_similarity=self.minimum_similarity,
        )

        return [
            Document(
                page_content=result.content,
                metadata={
                    "similarity": result.similarity,
                    "collection": result.collection,
                    "source": result.source,
                    "url": result.url,
                    "chunk_id": result.chunk_id,
                    "document_id": result.document_id,
                },
            )
            for result in response.results
        ]