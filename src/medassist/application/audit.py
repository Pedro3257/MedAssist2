"""
Define o registro de auditoria produzido pelo fluxo MedAssist.

O modelo contém somente dados sintéticos, metadados operacionais e
referências públicas. Segredos e respostas completas não são armazenados.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


AUDIT_DECISIONS = frozenset(
    {
        "blocked",
        "urgent",
        "patient_not_found",
        "insufficient_context",
        "human_validation",
        "provider_error",
        "completed",
    }
)


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """Representa uma execução completa que será persistida."""

    correlation_id: str
    patient_id: str | None
    question: str
    decision: str
    provider: str | None
    model: str | None
    sources: tuple[dict[str, object], ...]
    latency_ms: float | None
    requires_human_validation: bool
    error_code: str | None
    graph_events: tuple[dict[str, object], ...]

    def __post_init__(self) -> None:
        """Valida os campos antes de qualquer acesso ao banco."""
        try:
            UUID(self.correlation_id)
        except (ValueError, AttributeError) as error:
            raise ValueError(
                "correlation_id deve ser um UUID válido"
            ) from error

        if not self.question.strip():
            raise ValueError(
                "question não pode estar vazia"
            )

        if self.decision not in AUDIT_DECISIONS:
            raise ValueError(
                "decision não é permitida na auditoria"
            )

        if (
            self.latency_ms is not None
            and self.latency_ms < 0
        ):
            raise ValueError(
                "latency_ms não pode ser negativa"
            )


class AuditRepository(Protocol):
    """Define a porta de persistência utilizada pelo grafo."""

    def save(
        self,
        record: AuditRecord,
    ) -> int:
        """Persiste uma execução e retorna seu identificador."""
        ...