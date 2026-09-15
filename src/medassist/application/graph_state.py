"""
Define o estado tipado compartilhado pelos nós do fluxo LangGraph.

O estado começa com a identificação do paciente e a pergunta. Cada nó
acrescenta somente os resultados sob sua responsabilidade, como paciente,
evidências, resposta, decisão de rota e eventos de auditoria.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Literal, TypedDict

from langchain_core.documents import Document

from medassist.application.context_builder import GenerationContext
from medassist.application.contextual_answer import ContextualAnswer
from medassist.application.patient_context import PatientContext


GraphRoute = Literal[
    "continue",
    "blocked",
    "urgent",
    "patient_not_found",
    "insufficient_context",
    "provider_error",
    "human_validation",
    "completed",
]

class GraphAuditEvent(TypedDict):
    """Representa um evento provisório produzido durante a execução."""

    node: str
    outcome: str
    detail: str


class MedAssistGraphState(TypedDict, total=False):
    """
    Mantém os dados acumulados durante a execução do grafo.

    O uso de total=False permite que os nós preencham o estado
    progressivamente, sem exigir todos os campos no início.
    """

    # Dados obrigatórios recebidos na entrada.
    patient_id: str
    question: str

    # Identificador compartilhado por toda a execução.
    correlation_id: str

    # Instante monotônico usado somente para calcular a latência total.
    started_at_monotonic: float

    # Resultado da persistência final da auditoria.
    audit_event_id: int | None
    latency_ms: float | None
    
    # Resultado das validações e decisões de segurança.
    request_allowed: bool
    blocked_reason: str | None
    route: GraphRoute

    # Dados estruturados recuperados do PostgreSQL.
    patient_context: PatientContext | None

    # Documentos recuperados da base vetorial.
    documents: list[Document]

    # Contexto consolidado entregue à geração.
    generation_context: GenerationContext | None

    # Resposta estruturada produzida pelo serviço.
    answer: ContextualAnswer | None

    # Indica que a saída depende de revisão humana.
    requires_human_validation: bool

    # Mensagem explícita apresentada junto à decisão clínica.
    human_validation_message: str | None
    
    # Falha controlada ocorrida durante o fluxo.
    error: str | None

    # O reducer `add` acumula eventos em vez de substituir a lista.
    audit_events: Annotated[list[GraphAuditEvent], add]