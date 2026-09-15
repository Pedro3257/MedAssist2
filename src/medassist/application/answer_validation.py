"""
Valida respostas contextualizadas antes de sua apresentação.

A validação confirma estrutura, paciente, proveniência, limitações,
validação humana e ausência de instruções explícitas de dosagem.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from medassist.application.contextual_answer import ContextualAnswer


DOSAGE_OUTPUT_PATTERN = re.compile(
    r"\b(?:tome|use|administre|ingerir|take|administer)\s+"
    r"\d+(?:[.,]\d+)?\s*"
    r"(?:mg|mcg|g|ml|comprimidos?|cápsulas?|tablets?|capsules?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class AnswerValidationResult:
    """Representa o resultado da validação determinística da saída."""

    valid: bool
    reason: str | None
    safety_violation: bool = False


def _is_valid_url(value: str | None) -> bool:
    """Aceita somente URLs HTTP ou HTTPS com domínio."""
    if not value:
        return False

    parsed = urlparse(value)

    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
    )


def validate_contextual_answer(
    answer: ContextualAnswer,
    *,
    expected_patient_id: str,
) -> AnswerValidationResult:
    """
    Confirma que a resposta pode seguir para validação humana.

    O fallback é válido sem fontes. Uma resposta produzida por LLM
    precisa possuir fontes rastreáveis e metadados coerentes.
    """
    if not answer.answer_text.strip():
        return AnswerValidationResult(
            valid=False,
            reason="A resposta principal está vazia.",
        )

    if answer.patient_id != expected_patient_id:
        return AnswerValidationResult(
            valid=False,
            reason="A resposta pertence a outro paciente.",
        )

    if not answer.limitations.strip():
        return AnswerValidationResult(
            valid=False,
            reason="A resposta não apresenta limitações.",
        )

    if not answer.human_validation.strip():
        return AnswerValidationResult(
            valid=False,
            reason=(
                "A resposta não exige validação humana."
            ),
        )

    if DOSAGE_OUTPUT_PATTERN.search(answer.answer_text):
        return AnswerValidationResult(
            valid=False,
            reason=(
                "A resposta contém uma instrução explícita "
                "de dosagem."
            ),
            safety_violation=True,
        )

    if not answer.used_llm:
        if answer.provider != "fallback":
            return AnswerValidationResult(
                valid=False,
                reason=(
                    "Resposta sem LLM deve utilizar o provider fallback."
                ),
            )

        if answer.sources:
            return AnswerValidationResult(
                valid=False,
                reason=(
                    "O fallback não deve declarar fontes recuperadas."
                ),
            )

        return AnswerValidationResult(
            valid=True,
            reason=None,
        )

    if answer.provider == "fallback":
        return AnswerValidationResult(
            valid=False,
            reason=(
                "Resposta gerada por LLM não pode usar "
                "o provider fallback."
            ),
        )

    if not answer.model.strip() or answer.model == "none":
        return AnswerValidationResult(
            valid=False,
            reason="A resposta não informa o modelo utilizado.",
        )

    if not answer.sources:
        return AnswerValidationResult(
            valid=False,
            reason="A resposta gerada não apresenta fontes.",
        )

    positions: set[int] = set()

    for source in answer.sources:
        if source.position <= 0:
            return AnswerValidationResult(
                valid=False,
                reason="A fonte possui posição inválida.",
            )

        if source.position in positions:
            return AnswerValidationResult(
                valid=False,
                reason="A resposta contém posições de fonte duplicadas.",
            )

        positions.add(source.position)

        if not source.collection.strip():
            return AnswerValidationResult(
                valid=False,
                reason="A fonte não informa a coleção.",
            )

        if not source.source or not source.source.strip():
            return AnswerValidationResult(
                valid=False,
                reason="A fonte não informa sua origem.",
            )

        if not source.chunk_id.strip():
            return AnswerValidationResult(
                valid=False,
                reason="A fonte não informa o chunk.",
            )

        if not 0.0 <= source.similarity <= 1.0:
            return AnswerValidationResult(
                valid=False,
                reason="A fonte possui similaridade inválida.",
            )

        if not _is_valid_url(source.url):
            return AnswerValidationResult(
                valid=False,
                reason="A fonte não apresenta uma URL válida.",
            )

    return AnswerValidationResult(
        valid=True,
        reason=None,
    )