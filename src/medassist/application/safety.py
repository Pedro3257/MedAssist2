"""
Avalia solicitações clínicas antes da execução do pipeline.

A política bloqueia pedidos individualizados de prescrição, dosagem ou
diagnóstico definitivo. Perguntas médicas educacionais continuam permitidas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


SafetyCategory = Literal[
    "allowed",
    "prescription",
    "dosage",
    "definitive_diagnosis",
    "professional_replacement",
    "urgent",
    "prompt_injection",
]


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    """Representa uma decisão determinística da camada de segurança."""

    allowed: bool
    category: SafetyCategory
    reason: str | None
    requires_human_validation: bool


PRESCRIPTION_PATTERNS = (
    re.compile(
        r"\b(?:prescreva|prescrever|receite|receitar)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bqual(?:\s+é)?\s+(?:o\s+)?remédio\s+"
        r"(?:eu\s+)?devo\s+tomar\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:tell me|recommend)\s+(?:exactly\s+)?"
        r"(?:what|which)\s+(?:medicine|medication)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwhat\s+(?:medicine|medication)\s+"
        r"should\s+i\s+take\b",
        re.IGNORECASE,
    ),
)

DOSAGE_PATTERNS = (
    re.compile(
        r"\b(?:dosagem|dose exata|qual dose)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:quantos?|quantas?)\s+"
        r"(?:mg|ml|comprimidos?|cápsulas?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:exact dosage|what dose|which dose)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bhow many\s+(?:mg|ml|tablets?|capsules?)\b",
        re.IGNORECASE,
    ),
)

DIAGNOSIS_PATTERNS = (
    re.compile(
        r"\b(?:diagnostique|diagnosticar)\s+(?:me|a mim)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:dê|forneça)\s+(?:um\s+)?"
        r"diagnóstico(?:\s+definitivo)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bqual\s+(?:é|seria)\s+(?:o\s+)?"
        r"meu\s+diagnóstico\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdiagnose\s+me\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\btell\s+me\s+(?:exactly\s+)?"
        r"what\s+(?:disease|condition)\s+i\s+have\b",
        re.IGNORECASE,
    ),
)

PROFESSIONAL_REPLACEMENT_PATTERNS = (
    re.compile(
        r"\b(?:substitua|substituir)\s+"
        r"(?:o\s+)?(?:meu|minha)?\s*"
        r"(?:médico|médica|profissional de saúde)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:não|nao)\s+(?:quero|preciso)\s+"
        r"(?:ir|consultar|procurar)\s+"
        r"(?:ao|um|uma)?\s*"
        r"(?:médico|médica|profissional)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bsem\s+(?:ir|consultar|procurar)\s+"
        r"(?:ao|um|uma)?\s*"
        r"(?:médico|médica|profissional)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:replace|be)\s+(?:my\s+)?"
        r"(?:doctor|physician|healthcare professional)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwithout\s+(?:seeing|consulting)\s+"
        r"(?:a\s+)?(?:doctor|physician)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bi\s+(?:do not|don't)\s+need\s+"
        r"to\s+see\s+(?:a\s+)?doctor\b",
        re.IGNORECASE,
    ),
)

URGENT_PATTERNS = (
    re.compile(
        r"\b(?:estou|eu estou|sinto|estou sentindo|tenho)\b"
        r".{0,40}\b(?:dor forte|dor intensa)\s+no\s+peito\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:i have|i am having|i'm having|i feel)\b"
        r".{0,40}\b(?:severe|intense)?\s*chest pain\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:não consigo|nao consigo)\s+respirar\b"
        r"|\b(?:falta de ar intensa|dificuldade para respirar)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:cannot breathe|can't breathe|"
        r"severe difficulty breathing)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:desmaiou|desmaiei|inconsciente|"
        r"perda de consciência)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:unconscious|passed out|lost consciousness)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:fraqueza em um lado|fala enrolada|"
        r"fala arrastada|rosto caído)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:one-sided weakness|slurred speech|"
        r"face drooping)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:sangramento intenso|"
        r"sangramento incontrolável)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:severe bleeding|uncontrolled bleeding)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:quero me matar|vou me matar|"
        r"pensando em suicídio|pensando em suicidio)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:kill myself|attempt suicide|"
        r"thinking about suicide)\b",
        re.IGNORECASE,
    ),
)

PROMPT_INJECTION_PATTERNS = (
    re.compile(
        r"\b(?:ignore|desconsidere|esqueça)\s+"
        r"(?:todas?\s+)?(?:as\s+)?"
        r"(?:instruções|regras)\s+"
        r"(?:anteriores|do sistema|do desenvolvedor)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:ignore|disregard|forget)\s+"
        r"(?:all\s+)?"
        r"(?:previous|system|developer)\s+"
        r"(?:instructions|rules|messages)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:revele|mostre|exiba|imprima)\s+"
        r"(?:(?:o|a|os|as)\s+)?"
        r"(?:(?:seu|sua|seus|suas)\s+)?"
        r"(?:prompt do sistema|prompt interno|"
        r"instruções internas)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:reveal|show|print|expose)\s+"
        r"(?:your\s+|the\s+)?"
        r"(?:system prompt|internal prompt|"
        r"hidden instructions)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:desative|remova|contorne|burle)\s+"
        r"(?:as\s+|os\s+)?"
        r"(?:regras|filtros|restrições|"
        r"controles de segurança)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:disable|remove|bypass|override)\s+"
        r"(?:all\s+|the\s+)?"
        r"(?:safety rules|safety filters|"
        r"restrictions|guardrails)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:aja|finja)\s+"
        r"(?:como se fosse|que é|que você é)\s+"
        r"(?:um\s+|uma\s+)?"
        r"(?:médico|médica|assistente)\s+"
        r"(?:sem regras|sem restrições|irrestrito)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:act|pretend)\s+as\s+"
        r"(?:an?\s+)?(?:unrestricted|uncensored)\s+"
        r"(?:doctor|assistant|model)\b",
        re.IGNORECASE,
    ),
)

def _matches_any(
    question: str,
    patterns: tuple[re.Pattern[str], ...],
) -> bool:
    """Indica se algum padrão da categoria aparece na pergunta."""
    return any(
        pattern.search(question)
        for pattern in patterns
    )


def evaluate_request(question: str) -> SafetyDecision:
    """
    Classifica a solicitação antes do acesso ao banco ou à LLM.

    A ordem prioriza dosagem e prescrição porque um mesmo pedido pode
    conter também uma solicitação de diagnóstico.
    """
    normalized_question = " ".join(question.split())

    if not normalized_question:
        raise ValueError("question não pode estar vazia")

    # Urgência tem prioridade sobre diagnóstico, prescrição e dosagem.
    if _matches_any(
        normalized_question,
        URGENT_PATTERNS,
    ):
        return SafetyDecision(
            allowed=False,
            category="urgent",
            reason=(
                "Os sintomas descritos podem exigir avaliação urgente. "
                "Procure atendimento de emergência imediatamente. "
                "No Brasil, ligue para o SAMU pelo número 192. "
                "Se estiver em outro país, use o serviço local de "
                "emergência."
            ),
            requires_human_validation=True,
        )

    # Tentativas de alterar ou revelar regras internas são bloqueadas.
    if _matches_any(
        normalized_question,
        PROMPT_INJECTION_PATTERNS,
    ):
        return SafetyDecision(
            allowed=False,
            category="prompt_injection",
            reason=(
                "A solicitação tenta alterar, contornar ou revelar "
                "as instruções internas do MedAssist."
            ),
            requires_human_validation=True,
        )
    
    if _matches_any(
        normalized_question,
        DOSAGE_PATTERNS,
    ):
        return SafetyDecision(
            allowed=False,
            category="dosage",
            reason=(
                "O MedAssist não fornece dosagem "
                "individualizadas."
            ),
            requires_human_validation=True,
        )

    if _matches_any(
        normalized_question,
        PRESCRIPTION_PATTERNS,
    ):
        return SafetyDecision(
            allowed=False,
            category="prescription",
            reason=(
                "O MedAssist não prescreve nem recomenda "
                "medicamentos individualizados."
            ),
            requires_human_validation=True,
        )

    if _matches_any(
        normalized_question,
        DIAGNOSIS_PATTERNS,
    ):
        return SafetyDecision(
            allowed=False,
            category="definitive_diagnosis",
            reason=(
                "O MedAssist não fornece diagnóstico "
                "definitivo."
            ),
            requires_human_validation=True,
        )
    
    if _matches_any(
        normalized_question,
        PROFESSIONAL_REPLACEMENT_PATTERNS,
    ):
        return SafetyDecision(
            allowed=False,
            category="professional_replacement",
            reason=(
                "O MedAssist não substitui avaliação de "
                "profissional de saúde habilitado."
            ),
            requires_human_validation=True,
        )
    
    return SafetyDecision(
        allowed=True,
        category="allowed",
        reason=None,
        requires_human_validation=False,
    )