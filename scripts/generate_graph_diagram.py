"""
Gera um diagrama Mermaid a partir do workflow LangGraph compilado.

As dependências abaixo são substitutos que nunca acessam PostgreSQL,
Ollama ou Google AI. Elas existem somente para permitir a compilação
e a inspeção estrutural do grafo.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

from medassist.application.contextual_answer import ContextualAnswer
from medassist.application.graph_workflow import build_medassist_graph
from medassist.application.patient_context import PatientContext


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = (
    PROJECT_ROOT
    / "docs"
    / "diagrams"
    / "langgraph_flow.mmd"
)


class DiagramPatientRepository:
    """Representa o repositório sem executar consultas reais."""

    def get_by_id(
        self,
        patient_id: str,
    ) -> PatientContext | None:
        """Impede uso acidental durante a geração do diagrama."""
        raise RuntimeError(
            "O repositório não deve ser executado no diagrama."
        )


class DiagramRetriever:
    """Representa o retriever sem calcular embeddings."""

    def invoke(
        self,
        input: str,
    ) -> list[Document]:
        """Impede uso acidental durante a geração do diagrama."""
        raise RuntimeError(
            "O retriever não deve ser executado no diagrama."
        )


class DiagramAnswerService:
    """Representa a geração sem chamar qualquer provider."""

    def generate(self, **kwargs: object) -> ContextualAnswer:
        """Impede uso acidental durante a geração do diagrama."""
        raise RuntimeError(
            "O serviço não deve ser executado no diagrama."
        )


def main() -> None:
    """Compila o grafo e salva sua representação Mermaid."""
    graph = build_medassist_graph(
        repository=DiagramPatientRepository(),
        retriever=DiagramRetriever(),
        answer_service=DiagramAnswerService(),
        model="diagram-model",
    )

    mermaid = graph.get_graph().draw_mermaid()

    expected_nodes = {
        "validate_input",
        "safety",
        "patient",
        "retrieval",
        "context",
        "generation",
        "validate_answer",
        "human_review",
        "audit",
    }

    missing_nodes = {
        node
        for node in expected_nodes
        if node not in mermaid
    }

    if missing_nodes:
        raise RuntimeError(
            "Nós ausentes no diagrama: "
            + ", ".join(sorted(missing_nodes))
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    OUTPUT_FILE.write_text(
        mermaid,
        encoding="utf-8",
    )

    print("Diagrama Mermaid gerado com sucesso.")
    print(f"Arquivo: {OUTPUT_FILE}")
    print(f"Nós validados: {len(expected_nodes)}")


if __name__ == "__main__":
    main()