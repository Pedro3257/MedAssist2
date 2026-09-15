"""Gera e estrutura respostas contextualizadas com proveniência determinística."""

from __future__ import annotations

import re
from dataclasses import dataclass

from medassist.application.context_builder import GenerationContext, SourceReference
from medassist.application.generation_prompt import build_generation_messages
from medassist.application.llm import (
    LLMProvider,
    LLMProviderInvalidResponseError,
    LLMRequest,
)


PORTUGUESE_MARKERS = frozenset(
    {
        "como", "de", "do", "dos", "para", "qual", "quais", "que",
        "são", "tem", "tratamento",
    }
)
ENGLISH_MARKERS = frozenset(
    {
        "are", "can", "does", "for", "how", "is", "of", "the", "to",
        "treatment", "what", "when", "which", "with",
    }
)
SECTION_PATTERN = re.compile(
    r"(?im)^\s*(?:EVIDENCE USED|EVIDENCE RETRIEVED|SOURCES|"
    r"LIMITATIONS|HUMAN VALIDATION)\s*:\s*$"
)


@dataclass(frozen=True, slots=True)
class ContextualAnswer:
    """Mantém resposta, segurança e fontes em campos controlados pelo código."""

    answer_text: str
    patient_id: str
    sources: tuple[SourceReference, ...]
    limitations: str
    human_validation: str
    provider: str
    model: str
    used_llm: bool
    raw_model_content: str | None = None
    initial_model_content: str | None = None
    language_rewrite_performed: bool = False
    rewrite_model: str | None = None

    @property
    def abstained(self) -> bool:
        """Indica que nenhuma evidência permitiu chamar o LLM."""
        return not self.used_llm

    @property
    def content(self) -> str:
        """Renderiza sempre a mesma estrutura, independentemente do modelo."""
        if self.sources:
            evidence_lines = "\n".join(
                f"[Evidence {source.position}]" for source in self.sources
            )
            source_lines = "\n".join(
                f"[Evidence {source.position}] "
                f"{source.source or 'not informed'} | "
                f"{source.collection} | "
                f"{source.url or 'not informed'}"
                for source in self.sources
            )
        else:
            evidence_lines = "None"
            source_lines = "None"

        return (
            f"ANSWER:\n{self.answer_text}\n\n"
            f"EVIDENCE RETRIEVED:\n{evidence_lines}\n\n"
            f"SOURCES:\n{source_lines}\n\n"
            f"LIMITATIONS:\n{self.limitations}\n\n"
            f"HUMAN VALIDATION:\n{self.human_validation}"
        )


def _is_portuguese(question: str) -> bool:
    """Estima o idioma somente para os textos determinísticos de segurança."""
    normalized = question.casefold()
    if any(character in normalized for character in "áàâãéêíóôõúç"):
        return True
    words = set(re.findall(r"[a-z]+", normalized))
    return len(words & PORTUGUESE_MARKERS) >= 2


def _language_matches(question: str, answer: str) -> bool:
    """Compara o idioma provável da pergunta e da resposta gerada."""
    expected_portuguese = _is_portuguese(question)
    normalized = answer.casefold()
    words = set(re.findall(r"[a-z]+", normalized))
    answer_portuguese = (
        any(character in normalized for character in "áàâãéêíóôõúç")
        or len(words & PORTUGUESE_MARKERS) > len(words & ENGLISH_MARKERS)
    )
    return expected_portuguese == answer_portuguese


def _rewrite_instruction(
    question: str,
    context: GenerationContext,
    draft: str,
) -> str:
    """Cria uma revisão restrita ao idioma e às evidências fornecidas."""
    language = "Brazilian Portuguese" if _is_portuguese(question) else "English"
    return f"""
FINAL REVISION TASK

Required response language: {language}.

User question:
{question}

Draft answer in the wrong language:
{draft}

Available context:
{context.render()}

Rewrite the draft as a concise answer of at most 140 words in the required
language. Synthesize the relevant evidence instead of copying long passages.
Use only facts present in the available context. Do not add diagnoses,
treatments, dosages, anatomy or sources. Do not state that the patient has the
condition. Return only the answer body, without headings or source lists.
""".strip()


def _safety_texts(question: str, patient_id: str) -> tuple[str, str]:
    """Cria limitação e validação humana no idioma provável da pergunta."""
    if _is_portuguese(question):
        return (
            "As evidências oferecem informação médica geral e não permitem "
            f"estabelecer uma conclusão clínica sobre o paciente sintético {patient_id}.",
            "Qualquer decisão clínica requer validação por profissional de saúde "
            "habilitado.",
        )
    return (
        "The evidence provides general medical information and does not "
        f"establish a clinical conclusion about synthetic patient {patient_id}.",
        "Any clinical decision requires validation by a qualified healthcare "
        "professional.",
    )


def _clean_model_answer(content: str) -> str:
    """Extrai apenas a resposta principal quando o modelo cria seções próprias."""
    cleaned = content.strip()
    cleaned = re.sub(r"(?i)^\s*ANSWER\s*:\s*", "", cleaned, count=1)
    section = SECTION_PATTERN.search(cleaned)
    if section:
        cleaned = cleaned[: section.start()].rstrip()
    if not cleaned:
        raise LLMProviderInvalidResponseError(
            "O modelo retornou uma resposta principal vazia"
        )
    return cleaned


class ContextualAnswerService:
    """Conecta contexto, prompt e provider sem delegar estrutura ao LLM."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def generate(
        self,
        *,
        question: str,
        context: GenerationContext,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
        language_rewrite_model: str | None = None,
    ) -> ContextualAnswer:
        """Gera a narrativa e revisa uma vez quando o idioma diverge."""
        if not question.strip():
            raise ValueError("question não pode estar vazia")
        if not model.strip():
            raise ValueError("model não pode estar vazio")

        rewrite_model = (language_rewrite_model or model).strip()
        if not rewrite_model:
            raise ValueError("language_rewrite_model não pode estar vazio")

        limitations, human_validation = _safety_texts(
            question, context.patient_id
        )

        if not context.has_evidence:
            answer_text = (
                "Não foram recuperadas evidências suficientes para responder "
                "com segurança."
                if _is_portuguese(question)
                else "Insufficient evidence was retrieved to answer safely."
            )
            return ContextualAnswer(
                answer_text=answer_text,
                patient_id=context.patient_id,
                sources=(),
                limitations=limitations,
                human_validation=human_validation,
                provider="fallback",
                model="none",
                used_llm=False,
            )

        messages = build_generation_messages(question, context)
        if len(messages) != 2:
            raise RuntimeError("O prompt deve produzir mensagens system e human")

        system_content = messages[0].content
        user_content = messages[1].content
        if not isinstance(system_content, str):
            raise RuntimeError("A mensagem system deve conter texto")
        if not isinstance(user_content, str):
            raise RuntimeError("A mensagem human deve conter texto")

        response = self.provider.generate(
            LLMRequest(
                system_prompt=system_content,
                user_prompt=user_content,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                correlation_id=f"contextual-answer-{context.patient_id}",
            )
        )

        initial_content = response.content
        final_response = response
        rewrite_performed = False

        if not _language_matches(question, initial_content):
            final_response = self.provider.generate(
                LLMRequest(
                    system_prompt=system_content,
                    user_prompt=_rewrite_instruction(
                        question,
                        context,
                        initial_content,
                    ),
                    model=rewrite_model,
                    temperature=0.0,
                    max_tokens=min(max_tokens, 256),
                    correlation_id=(
                        f"contextual-answer-rewrite-{context.patient_id}"
                    ),
                )
            )
            rewrite_performed = True

        return ContextualAnswer(
            answer_text=_clean_model_answer(final_response.content),
            patient_id=context.patient_id,
            sources=context.sources,
            limitations=limitations,
            human_validation=human_validation,
            provider=final_response.provider,
            model=model,
            used_llm=True,
            raw_model_content=final_response.content,
            initial_model_content=initial_content,
            language_rewrite_performed=rewrite_performed,
            rewrite_model=(final_response.model if rewrite_performed else None),
        )