"""
Monta e compila o fluxo LangGraph completo do MedAssist.

O grafo coordena validação, segurança, paciente, RAG, contexto,
geração, validação humana, tratamento de falhas e auditoria.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from medassist.application.contextual_answer import ContextualAnswerService
from medassist.application.graph_nodes import (
    EvidenceRetriever,
    PatientRepository,
    create_audit_node,
    build_context_node,
    create_generation_node,
    create_patient_node,
    create_retrieval_node,
    human_validation_node,
    safety_node,
    validate_answer_node,
    validate_input_node,
)
from medassist.application.graph_state import MedAssistGraphState

# Importa a porta de persistência, sem acoplar o grafo ao PostgreSQL.
from medassist.application.audit import AuditRepository

def route_after_input_validation(state: MedAssistGraphState) -> str:
    """Seleciona segurança ou auditoria após validar a entrada."""
    route = state.get("route")
    if route == "continue":
        return "safety"
    if route == "blocked":
        return "audit"
    raise RuntimeError(f"Rota inesperada após validação de entrada: {route}")


def route_after_safety(
    state: MedAssistGraphState,
) -> str:
    """Seleciona paciente ou validação humana após segurança."""
    route = state.get("route")

    if route == "continue":
        return "patient"

    if route in {
        "blocked",
        "urgent",
    }:
        return "human_review"

    raise RuntimeError(
        f"Rota inesperada após segurança: {route}"
    )


def route_after_patient(state: MedAssistGraphState) -> str:
    """Seleciona recuperação ou auditoria após consultar o paciente."""
    route = state.get("route")
    if route == "continue":
        return "retrieval"
    if route == "patient_not_found":
        return "audit"
    raise RuntimeError(f"Rota inesperada após consulta do paciente: {route}")


def route_after_generation(state: MedAssistGraphState) -> str:
    """Seleciona validação da resposta ou auditoria após geração."""
    route = state.get("route")
    if route == "continue":
        return "validate_answer"
    
    if route == "provider_error":
        return "human_review"
    
    raise RuntimeError(f"Rota inesperada após geração: {route}")


def route_after_answer_validation(
    state: MedAssistGraphState,
) -> str:
    """Encaminha toda resposta clínica para validação humana."""
    route = state.get("route")

    if route in {
        "blocked",
        "human_validation",
        "insufficient_context",
        "provider_error",
    }:
        return "human_review"

    raise RuntimeError(
        f"Rota inesperada após validar a resposta: {route}"
    )

def build_medassist_graph(
    *,
    repository: PatientRepository,
    retriever: EvidenceRetriever,
    answer_service: ContextualAnswerService,
    model: str,
    language_rewrite_model: str | None = None,
    max_tokens: int = 512,
    audit_repository: AuditRepository | None = None,
    provider_name: str | None = None,
    minimize_remote_context: bool = False,
) -> CompiledStateGraph:
    """Compila o grafo completo com dependências injetadas."""
    builder = StateGraph(MedAssistGraphState)

    builder.add_node("validate_input", validate_input_node)
    builder.add_node("safety", safety_node)
    builder.add_node("patient", create_patient_node(repository))
    builder.add_node("retrieval", create_retrieval_node(retriever))
    builder.add_node("context", build_context_node)
    builder.add_node(
        "generation",
        create_generation_node(
            answer_service,
            model=model,
            language_rewrite_model=language_rewrite_model,
            max_tokens=max_tokens,
            minimize_remote_context=minimize_remote_context,
        ),
    )
    builder.add_node("validate_answer", validate_answer_node)
    builder.add_node(
        "human_review",
        human_validation_node,
    )
    builder.add_node(
        "audit",
        create_audit_node(
            audit_repository,
            provider_name=provider_name,
            configured_model=model,
        ),
    )

    builder.add_edge(START, "validate_input")
    builder.add_conditional_edges(
        "validate_input",
        route_after_input_validation,
        {"safety": "safety", "audit": "audit"},
    )
    builder.add_conditional_edges(
        "safety",
        route_after_safety,
        {
            "patient": "patient",
            "human_review": "human_review",
        },
    )
    builder.add_conditional_edges(
        "patient",
        route_after_patient,
        {"retrieval": "retrieval", "audit": "audit"},
    )
    builder.add_edge("retrieval", "context")
    builder.add_edge("context", "generation")
    builder.add_conditional_edges(
        "generation",
        route_after_generation,
        {
            "validate_answer": "validate_answer",
            "human_review": "human_review",
        },
    )
    builder.add_conditional_edges(
        "validate_answer",
        route_after_answer_validation,
        {
            "human_review": "human_review",
        },
    )
    builder.add_edge(
        "human_review",
        "audit",
    )
    builder.add_edge("audit", END)

    return builder.compile()
