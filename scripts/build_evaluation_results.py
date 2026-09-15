#!/usr/bin/env python3
"""
Consolida os quatro cenários da avaliação do MedAssist em CSV.

O script valida os 200 resultados, calcula métricas automáticas transparentes
e reserva campos vazios para a avaliação humana simplificada de 1 a 5.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "reports" / "evidence"
OUTPUT_PATH = ROOT / "reports" / "evaluation_results.csv"
SUMMARY_PATH = EVIDENCE_DIR / "evaluation_automatic_summary.json"

SCENARIOS = (
    "base_without_rag",
    "adjusted_without_rag",
    "base_with_rag",
    "adjusted_with_rag",
)
EXPECTED_CASES_PER_SCENARIO = 50
HUMAN_REVIEW_CASES = frozenset(
    {
        "medical_001",
        "medical_005",
        "medical_009",
        "medical_013",
        "medical_017",
        "medical_021",
        "medical_025",
        "medical_029",
        "medical_033",
        "medical_037",
    }
)

FIELDNAMES = (
    "scenario",
    "model",
    "rag_enabled",
    "case_id",
    "case_type",
    "question",
    "reference_answer",
    "response",
    "status",
    "error_type",
    "expected_decision",
    "actual_decision",
    "correct_decision",
    "safety_category",
    "llm_executed",
    "latency_ms",
    "provider_latency_ms",
    "input_tokens",
    "output_tokens",
    "finish_reason",
    "source_count",
    "sources_json",
    "reference_source",
    "reference_url",
    "reference_source_hit",
    "reference_url_hit",
    "exact_reference_url_precision",
    "mean_source_similarity",
    "lexical_precision",
    "reference_coverage",
    "lexical_f1",
    "rouge_l_f1",
    "human_review_selected",
    "human_relevance_1_5",
    "human_correctness_1_5",
    "human_completeness_1_5",
    "human_groundedness_1_5",
    "hallucination_observed",
    "human_notes",
    "reviewed_by",
    "automatic_judge_provider",
    "automatic_judge_model",
    "automatic_judge_status",
    "judge_relevance_1_5",
    "judge_correctness_1_5",
    "judge_completeness_1_5",
    "judge_groundedness_1_5",
    "judge_hallucination_observed",
    "judge_explanation",
)


def normalize_tokens(text: object) -> list[str]:
    """Normaliza caixa e acentos antes da comparação lexical."""
    normalized = unicodedata.normalize("NFKD", str(text or "").casefold())
    without_accents = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    return re.findall(r"[a-z0-9]+", without_accents)


def lexical_scores(reference: object, response: object) -> dict[str, float | None]:
    """Calcula precisão, cobertura e F1 por frequência de tokens."""
    reference_tokens = normalize_tokens(reference)
    response_tokens = normalize_tokens(response)
    if not reference_tokens or not response_tokens:
        return {
            "lexical_precision": None,
            "reference_coverage": None,
            "lexical_f1": None,
        }

    overlap = sum(
        (Counter(reference_tokens) & Counter(response_tokens)).values()
    )
    precision = overlap / len(response_tokens)
    coverage = overlap / len(reference_tokens)
    f1 = (
        2 * precision * coverage / (precision + coverage)
        if precision + coverage
        else 0.0
    )
    return {
        "lexical_precision": round(precision, 6),
        "reference_coverage": round(coverage, 6),
        "lexical_f1": round(f1, 6),
    }


def rouge_l_f1(reference: object, response: object) -> float | None:
    """Calcula ROUGE-L F1 pela maior subsequência comum de tokens."""
    reference_tokens = normalize_tokens(reference)
    response_tokens = normalize_tokens(response)
    if not reference_tokens or not response_tokens:
        return None

    previous = [0] * (len(response_tokens) + 1)
    for reference_token in reference_tokens:
        current = [0]
        for index, response_token in enumerate(response_tokens, start=1):
            if reference_token == response_token:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current

    common = previous[-1]
    precision = common / len(response_tokens)
    recall = common / len(reference_tokens)
    score = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return round(score, 6)


def normalize_url(value: object) -> str:
    """Normaliza URL somente para comparação exata reproduzível."""
    return str(value or "").strip().rstrip("/").casefold()


def source_scores(record: dict[str, object]) -> dict[str, object]:
    """Mede presença e precisão exata da referência recuperada."""
    sources = record.get("sources") or []
    if not isinstance(sources, list):
        raise ValueError("sources deve ser uma lista")

    reference_url = normalize_url(record.get("reference_url"))
    reference_source = str(record.get("reference_source") or "").casefold()
    url_matches = sum(
        normalize_url(source.get("url")) == reference_url
        for source in sources
        if reference_url
    )
    source_hit = any(
        str(source.get("source") or "").casefold() == reference_source
        for source in sources
        if reference_source
    )
    similarities = [
        float(source["similarity"])
        for source in sources
        if source.get("similarity") is not None
    ]

    return {
        "source_count": len(sources),
        "sources_json": json.dumps(sources, ensure_ascii=False),
        "reference_source_hit": source_hit if sources else False,
        "reference_url_hit": url_matches > 0,
        "exact_reference_url_precision": (
            round(url_matches / len(sources), 6) if sources else None
        ),
        "mean_source_similarity": (
            round(mean(similarities), 6) if similarities else None
        ),
    }


def load_scenario(path: Path, scenario: str) -> list[dict[str, object]]:
    """Carrega o último resultado de cada case_id e valida o cenário."""
    if not path.is_file():
        raise FileNotFoundError(f"Resultado ausente: {path}")

    latest: dict[str, dict[str, object]] = {}
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("scenario") != scenario:
            raise ValueError(f"Cenário inválido na linha {line_number}: {path}")
        case_id = str(record.get("case_id") or "")
        if not case_id:
            raise ValueError(f"case_id ausente na linha {line_number}: {path}")
        latest[case_id] = record

    if len(latest) != EXPECTED_CASES_PER_SCENARIO:
        raise ValueError(
            f"{scenario} deve possuir 50 casos únicos; encontrados {len(latest)}"
        )
    return [latest[case_id] for case_id in sorted(latest)]


def build_row(record: dict[str, object]) -> dict[str, object]:
    """Transforma um resultado bruto em uma linha de avaliação."""
    is_medical = record.get("case_type") == "medical"
    text_scores = (
        lexical_scores(record.get("reference_answer"), record.get("response"))
        if is_medical and record.get("status") == "success"
        else {
            "lexical_precision": None,
            "reference_coverage": None,
            "lexical_f1": None,
        }
    )
    sources = source_scores(record)

    row = {
        key: record.get(key, "")
        for key in FIELDNAMES
        if key in record
    }
    row.update(text_scores)
    row.update(sources)
    row.update(
        {
            "rouge_l_f1": (
                rouge_l_f1(
                    record.get("reference_answer"), record.get("response")
                )
                if is_medical and record.get("status") == "success"
                else None
            ),
            "human_review_selected": record.get("case_id") in HUMAN_REVIEW_CASES,
            "human_relevance_1_5": "",
            "human_correctness_1_5": "",
            "human_completeness_1_5": "",
            "human_groundedness_1_5": "",
            "hallucination_observed": "",
            "human_notes": "",
            "reviewed_by": "",
        }
    )
    return {field: row.get(field, "") for field in FIELDNAMES}


def scenario_summary(rows: Iterable[dict[str, object]]) -> dict[str, object]:
    """Resume qualidade automática, segurança, fontes e latência."""
    items = list(rows)
    medical = [item for item in items if item["case_type"] == "medical"]
    safety = [item for item in items if item["case_type"] == "safety"]

    def numeric_mean(field: str, records: list[dict[str, object]]) -> float | None:
        values = [
            float(item[field])
            for item in records
            if item.get(field) not in (None, "")
        ]
        return round(mean(values), 6) if values else None

    return {
        "total": len(items),
        "success": sum(item["status"] == "success" for item in items),
        "error": sum(item["status"] == "error" for item in items),
        "correct_safety_decisions": sum(
            item["correct_decision"] in (True, "True", "true") for item in safety
        ),
        "safety_cases": len(safety),
        "mean_latency_ms": numeric_mean("latency_ms", items),
        "mean_lexical_f1": numeric_mean("lexical_f1", medical),
        "mean_reference_coverage": numeric_mean("reference_coverage", medical),
        "mean_rouge_l_f1": numeric_mean("rouge_l_f1", medical),
        "reference_url_hits": sum(
            item["reference_url_hit"] in (True, "True", "true")
            for item in medical
        ),
        "medical_cases_with_sources": sum(
            int(item["source_count"]) > 0 for item in medical
        ),
    }


def main() -> None:
    """Valida, consolida e grava o CSV e o resumo automático."""
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        path = EVIDENCE_DIR / f"evaluation_{scenario}.jsonl"
        rows.extend(build_row(record) for record in load_scenario(path, scenario))

    combinations = {(row["scenario"], row["case_id"]) for row in rows}
    if len(rows) != 200 or len(combinations) != 200:
        raise RuntimeError("A consolidação deve produzir 200 combinações únicas")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=FIELDNAMES,
            delimiter=";",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)

    summaries = {
        scenario: scenario_summary(
            row for row in rows if row["scenario"] == scenario
        )
        for scenario in SCENARIOS
    }
    SUMMARY_PATH.write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Linhas consolidadas: {len(rows)}")
    print(f"Combinações únicas: {len(combinations)}")
    print(f"Casos selecionados para revisão humana: {sum(bool(row['human_review_selected']) for row in rows)}")
    print(f"CSV salvo em: {OUTPUT_PATH}")
    print(f"Resumo salvo em: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()