"""
Implementa os nós do fluxo LangGraph do MedAssist.

Nesta primeira etapa, os nós validam e normalizam a entrada e aplicam
uma verificação inicial de segurança. Cada nó retorna somente os campos
que devem ser atualizados no estado compartilhado.
"""

from __future__ import annotations

import re
from uuid import uuid4

from medassist.application.graph_state import MedAssistGraphState

# Importa os contratos necessários para criar nós com dependências injetadas.
from collections.abc import Callable
from typing import Protocol

from langchain_core.documents import Document

from medassist.application.context_builder import (
    build_generation_context,
)
from medassist.application.patient_context import PatientContext

# Importa o serviço de geração e o erro comum dos providers.
from medassist.application.contextual_answer import (
    ContextualAnswerService,
)
from medassist.application.llm import LLMProviderError

# Importa a política clínica reutilizável da aplicação.
from medassist.application.safety import evaluate_request

# Importa a validação determinística da resposta estruturada.
from medassist.application.answer_validation import (
    validate_contextual_answer,
)

# Utiliza relógio monotônico para calcular duração sem depender do horário.
from time import perf_counter

# Importa o registro e a porta de persistência da auditoria.
from medassist.application.audit import (
    AuditRecord,
    AuditRepository,
)

# Minimiza o contexto quando a geração utiliza provider remoto.
from medassist.application.privacy import (
    minimize_generation_context,
)

# Redige credenciais acidentalmente presentes antes de persistir auditoria.
from medassist.application.redaction import (
    redact_audit_events,
    redact_secrets,
)

PATIENT_ID_PATTERN = re.compile(r"^PAT-[0-9]{3}$")

class PatientRepository(Protocol):
    """Define somente a operação de paciente necessária pelo grafo."""

    def get_by_id(
        self,
        patient_id: str,
    ) -> PatientContext | None:
        """Retorna o contexto do paciente ou None quando não existe."""
        ...


class EvidenceRetriever(Protocol):
    """Define a operação de recuperação utilizada pelo grafo."""

    def invoke(
        self,
        input: str,
    ) -> list[Document]:
        """Recupera documentos relevantes para a pergunta."""
        ...


def validate_input_node(
    state: MedAssistGraphState,
) -> dict[str, object]:
    """
    Normaliza e valida o identificador do paciente e a pergunta.

    Entradas inválidas são transformadas em uma rota controlada, evitando
    que banco, embeddings ou LLM sejam chamados desnecessariamente.
    """
    patient_id = state.get("patient_id", "").strip().upper()
    question = state.get("question", "").strip()
    correlation_id = state.get("correlation_id") or str(uuid4())
    started_at_monotonic = state.get(
        "started_at_monotonic",
        perf_counter(),
    )

    if not PATIENT_ID_PATTERN.fullmatch(patient_id):
        return {
            "patient_id": patient_id,
            "question": question,
            "correlation_id": correlation_id,
            "started_at_monotonic": started_at_monotonic,
            "request_allowed": False,
            "blocked_reason": (
                "patient_id deve seguir o formato PAT-000"
            ),
            "route": "blocked",
            "audit_events": [
                {
                    "node": "validate_input",
                    "outcome": "blocked",
                    "detail": "Identificador de paciente inválido.",
                }
            ],
        }

    if not question:
        return {
            "patient_id": patient_id,
            "question": question,
            "correlation_id": correlation_id,
            "started_at_monotonic": started_at_monotonic,
            "request_allowed": False,
            "blocked_reason": "A pergunta não pode estar vazia.",
            "route": "blocked",
            "audit_events": [
                {
                    "node": "validate_input",
                    "outcome": "blocked",
                    "detail": "Pergunta vazia.",
                }
            ],
        }

    return {
        "patient_id": patient_id,
        "question": question,
        "correlation_id": correlation_id,
        "started_at_monotonic": started_at_monotonic,
        "request_allowed": True,
        "blocked_reason": None,
        "route": "continue",
        "audit_events": [
            {
                "node": "validate_input",
                "outcome": "accepted",
                "detail": "Entrada normalizada e validada.",
            }
        ],
    }

def safety_node(
    state: MedAssistGraphState,
) -> dict[str, object]:
    """
    Aplica a política clínica antes do banco, RAG e LLM.

    Pedidos individualizados proibidos seguem para a rota bloqueada.
    Perguntas educacionais continuam pelo fluxo principal.
    """
    decision = evaluate_request(
        state.get("question", "")
    )

    if not decision.allowed:
        route = (
            "urgent"
            if decision.category == "urgent"
            else "blocked"
        )

        return {
            "request_allowed": False,
            "blocked_reason": decision.reason,
            "route": route,
            "requires_human_validation": (
                decision.requires_human_validation
            ),
            "audit_events": [
                {
                    "node": "safety",
                    "outcome": route,
                    "detail": (
                        "Solicitação classificada na categoria "
                        f"{decision.category}."
                    ),
                }
            ],
        }
    
        return {
            "request_allowed": False,
            "blocked_reason": decision.reason,
            "route": "blocked",
            "requires_human_validation": (
                decision.requires_human_validation
            ),
            "audit_events": [
                {
                    "node": "safety",
                    "outcome": "blocked",
                    "detail": (
                        "Solicitação bloqueada pela categoria "
                        f"{decision.category}."
                    ),
                }
            ],
        }

    return {
        "request_allowed": True,
        "blocked_reason": None,
        "route": "continue",
        "audit_events": [
            {
                "node": "safety",
                "outcome": "accepted",
                "detail": (
                    "Solicitação educacional permitida."
                ),
            }
        ],
    }

def create_patient_node(
    repository: PatientRepository,
) -> Callable[[MedAssistGraphState], dict[str, object]]:
    """
    Cria o nó que consulta o paciente e seus exames no PostgreSQL.

    A dependência é recebida externamente para permitir testes unitários
    sem conexão real com o banco de dados.
    """

    def patient_node(
        state: MedAssistGraphState,
    ) -> dict[str, object]:
        """Recupera somente o paciente solicitado no estado."""
        patient_id = state["patient_id"]
        patient_context = repository.get_by_id(patient_id)

        if patient_context is None:
            return {
                "patient_context": None,
                "route": "patient_not_found",
                "audit_events": [
                    {
                        "node": "patient",
                        "outcome": "not_found",
                        "detail": (
                            "Paciente sintético não encontrado."
                        ),
                    }
                ],
            }

        return {
            "patient_context": patient_context,
            "route": "continue",
            "audit_events": [
                {
                    "node": "patient",
                    "outcome": "found",
                    "detail": (
                        "Paciente e exames sintéticos recuperados."
                    ),
                }
            ],
        }

    return patient_node

def create_retrieval_node(
    retriever: EvidenceRetriever,
) -> Callable[[MedAssistGraphState], dict[str, object]]:
    """
    Cria o nó que recupera evidências médicas usando o retriever LangChain.

    O nó define a rota de contexto insuficiente quando nenhum documento
    supera o limiar de similaridade configurado no retriever.
    """

    def retrieval_node(
        state: MedAssistGraphState,
    ) -> dict[str, object]:
        """Recupera documentos relacionados à pergunta validada."""
        documents = list(
            retriever.invoke(state["question"])
        )

        if not documents:
            return {
                "documents": [],
                "route": "insufficient_context",
                "audit_events": [
                    {
                        "node": "retrieval",
                        "outcome": "insufficient_context",
                        "detail": (
                            "Nenhuma evidência atingiu o limiar mínimo."
                        ),
                    }
                ],
            }

        return {
            "documents": documents,
            "route": "continue",
            "audit_events": [
                {
                    "node": "retrieval",
                    "outcome": "evidence_found",
                    "detail": (
                        f"{len(documents)} evidência(s) recuperada(s)."
                    ),
                }
            ],
        }

    return retrieval_node

def build_context_node(
    state: MedAssistGraphState,
) -> dict[str, object]:
    """
    Combina o paciente sintético e as evidências recuperadas.

    O resultado mantém o prontuário separado do conhecimento médico,
    evitando tratar evidências gerais como diagnóstico do paciente.
    """
    patient_context = state.get("patient_context")

    if patient_context is None:
        raise RuntimeError(
            "O contexto não pode ser criado sem paciente."
        )

    generation_context = build_generation_context(
        patient_context,
        state.get("documents", []),
    )

    return {
        "generation_context": generation_context,
        "route": (
            "continue"
            if generation_context.has_evidence
            else "insufficient_context"
        ),
        "audit_events": [
            {
                "node": "context",
                "outcome": (
                    "ready"
                    if generation_context.has_evidence
                    else "insufficient_context"
                ),
                "detail": (
                    f"{len(generation_context.sources)} "
                    "fonte(s) adicionada(s) ao contexto."
                ),
            }
        ],
    }

def create_generation_node(
    answer_service: ContextualAnswerService,
    *,
    model: str,
    language_rewrite_model: str | None = None,
    max_tokens: int = 512,
    minimize_remote_context: bool = False,
) -> Callable[[MedAssistGraphState], dict[str, object]]:
    """
    Cria o nó que produz a resposta contextualizada.

    O mesmo nó também produz o fallback determinístico quando o contexto
    não possui evidências, sem realizar chamada ao provider.
    """
    if not model.strip():
        raise ValueError("model não pode estar vazio")

    if max_tokens <= 0:
        raise ValueError("max_tokens deve ser maior que zero")

    def generation_node(
        state: MedAssistGraphState,
    ) -> dict[str, object]:
        """Gera a resposta ou registra uma falha controlada do provider."""
        generation_context = state.get("generation_context")

        if generation_context is None:
            raise RuntimeError(
                "A geração exige um contexto previamente construído."
            )

        effective_context = generation_context

        if minimize_remote_context:
            patient_context = state.get(
                "patient_context"
            )

            if patient_context is None:
                raise RuntimeError(
                    "A minimização exige o contexto do paciente."
                )

            effective_context = minimize_generation_context(
                generation_context,
                patient_context,
            )

        try:
            answer = answer_service.generate(
                question=state["question"],
                context=effective_context,
                model=model,
                temperature=0.0,
                max_tokens=max_tokens,
                language_rewrite_model=language_rewrite_model,
            )
        except LLMProviderError as error:
            return {
                "answer": None,
                "error": type(error).__name__,
                "route": "provider_error",
                "requires_human_validation": True,
                "audit_events": [
                    {
                        "node": "generation",
                        "outcome": "provider_error",
                        "detail": (
                            "O provider não conseguiu gerar a resposta."
                        ),
                    }
                ],
            }

        return {
            "answer": answer,
            "error": None,
            "route": "continue",
            "audit_events": [
                {
                    "node": "generation",
                    "outcome": (
                        "fallback"
                        if answer.abstained
                        else "generated"
                    ),
                    "detail": (
                        "Resposta contextualizada criada."
                        if answer.used_llm
                        else "Fallback criado sem executar a LLM."
                    ),
                }
            ],
        }

    return generation_node

def validate_answer_node(
    state: MedAssistGraphState,
) -> dict[str, object]:
    """
    Valida estrutura, paciente, segurança e proveniência da resposta.

    Falhas estruturais seguem como provider_error. Uma instrução explícita
    de dosagem produz bloqueio de segurança.
    """
    answer = state.get("answer")

    if answer is None:
        return {
            "route": "provider_error",
            "requires_human_validation": True,
            "error": state.get("error") or "Resposta ausente.",
            "audit_events": [
                {
                    "node": "validate_answer",
                    "outcome": "invalid",
                    "detail": "Nenhuma resposta foi produzida.",
                }
            ],
        }

    validation = validate_contextual_answer(
        answer,
        expected_patient_id=state["patient_id"],
    )

    if not validation.valid:
        route = (
            "blocked"
            if validation.safety_violation
            else "provider_error"
        )

        return {
            "route": route,
            "requires_human_validation": True,
            "error": validation.reason,
            "audit_events": [
                {
                    "node": "validate_answer",
                    "outcome": route,
                    "detail": (
                        "A resposta estruturada não passou "
                        "pela validação."
                    ),
                }
            ],
        }

    route = (
        "insufficient_context"
        if answer.abstained
        else "human_validation"
    )

    return {
        "route": route,
        "requires_human_validation": True,
        "error": None,
        "audit_events": [
            {
                "node": "validate_answer",
                "outcome": "valid",
                "detail": (
                    "Resposta estruturada validada e encaminhada "
                    "para revisão humana."
                ),
            }
        ],
    }

def human_validation_node(
    state: MedAssistGraphState,
) -> dict[str, object]:
    """
    Marca explicitamente que a decisão requer validação humana.

    O nó não aprova automaticamente nenhuma conduta e preserva a rota
    que descreve o resultado anterior do fluxo.
    """
    route = state.get("route")

    if route not in {
        "blocked",
        "urgent",
        "insufficient_context",
        "human_validation",
        "provider_error",
    }:
        raise RuntimeError(
            "A validação humana recebeu uma rota inesperada: "
            f"{route}"
        )

    return {
        "requires_human_validation": True,
        "human_validation_message": (
            "Esta resposta não constitui diagnóstico, prescrição ou "
            "conduta clínica autônoma. Qualquer decisão deve ser "
            "validada por profissional de saúde habilitado."
        ),
        "audit_events": [
            {
                "node": "human_review",
                "outcome": "required",
                "detail": (
                    "Execução encaminhada para validação humana."
                ),
            }
        ],
    }

def audit_node(
    state: MedAssistGraphState,
) -> dict[str, object]:
    """
    Executa auditoria somente em memória.

    Esta função preserva compatibilidade com os testes unitários. O grafo
    utiliza create_audit_node para ativar persistência quando configurada.
    """
    return create_audit_node()(state)

def create_audit_node(
    repository: AuditRepository | None = None,
    *,
    provider_name: str | None = None,
    configured_model: str | None = None,
    clock: Callable[[], float] = perf_counter,
) -> Callable[[MedAssistGraphState], dict[str, object]]:
    """
    Cria o nó final de auditoria com persistência opcional.

    Sem repositório, o nó mantém somente a auditoria em memória. Com
    repositório, converte o estado final em AuditRecord e salva no banco.
    """

    def persistent_audit_node(
        state: MedAssistGraphState,
    ) -> dict[str, object]:
        """Calcula latência, monta o registro e persiste a execução."""
        route = state.get("route", "provider_error")
        started_at = state.get("started_at_monotonic")
        latency_ms = (
            max(0.0, (clock() - started_at) * 1000)
            if started_at is not None
            else None
        )

        final_event = {
            "node": "audit",
            "outcome": route,
            "detail": (
                "Execução finalizada com decisão controlada."
            ),
        }

        result: dict[str, object] = {
            "latency_ms": latency_ms,
            "audit_events": [final_event],
        }

        if repository is None:
            return result

        answer = state.get("answer")

        if answer is not None:
            effective_provider = answer.provider
            effective_model = answer.model
            sources = tuple(
                {
                    "position": source.position,
                    "collection": source.collection,
                    "source": source.source,
                    "url": source.url,
                    "chunk_id": source.chunk_id,
                    "similarity": source.similarity,
                }
                for source in answer.sources
            )
        else:
            effective_provider = provider_name
            effective_model = configured_model
            sources = ()

        patient_id = state.get("patient_id")

        if (
            patient_id is not None
            and not PATIENT_ID_PATTERN.fullmatch(patient_id)
        ):
            patient_id = None

        question = redact_secrets(
            state.get("question", "").strip()
        )

        if not question:
            question = "[empty question]"

        graph_events = redact_audit_events(tuple(
            dict(event)
            for event in (
                *state.get("audit_events", []),
                final_event,
            )
        ))

        record = AuditRecord(
            correlation_id=state["correlation_id"],
            patient_id=patient_id,
            question=question,
            decision=route,
            provider=effective_provider,
            model=effective_model,
            sources=sources,
            latency_ms=latency_ms,
            requires_human_validation=state.get(
                "requires_human_validation",
                False,
            ),
            error_code=redact_secrets(state.get("error")),
            graph_events=graph_events,
        )

        result["audit_event_id"] = repository.save(
            record
        )

        return result

    return persistent_audit_node