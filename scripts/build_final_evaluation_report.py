#!/usr/bin/env python3
"""Gera tabelas, gráficos e análise final da avaliação comparativa."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean

from build_preliminary_evaluation_charts import write_grouped_chart


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports" / "evaluation_results.csv"
EVIDENCE_DIR = ROOT / "reports" / "evidence"
FIGURES_DIR = ROOT / "reports" / "figures"
SUMMARY_PATH = EVIDENCE_DIR / "evaluation_final_summary.csv"
AGREEMENT_PATH = EVIDENCE_DIR / "evaluation_judge_agreement.csv"
REPORT_PATH = ROOT / "reports" / "day12_final_analysis.md"
SCENARIOS = (
    "base_without_rag",
    "adjusted_without_rag",
    "base_with_rag",
    "adjusted_with_rag",
)
LABELS = {
    "base_without_rag": "Base sem RAG",
    "adjusted_without_rag": "Ajustado sem RAG",
    "base_with_rag": "Base com RAG",
    "adjusted_with_rag": "Ajustado com RAG",
}


def load_selected_rows() -> list[dict[str, str]]:
    """Carrega e valida os 40 casos qualitativos consolidados no CSV."""
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as stream:
        rows = [
            row for row in csv.DictReader(stream, delimiter=";")
            if row["human_review_selected"].casefold() == "true"
        ]
    if len(rows) != 40:
        raise ValueError(f"Esperados 40 casos qualitativos; encontrados {len(rows)}")
    if any(row["automatic_judge_status"] != "success" for row in rows):
        raise ValueError("Todos os 40 julgamentos devem estar concluídos")
    if {row["automatic_judge_model"] for row in rows} != {"qwen2.5:7b-instruct"}:
        raise ValueError("O CSV deve conter somente o avaliador Qwen definido")
    return rows


def average(rows: list[dict[str, str]], field: str) -> float | None:
    """Calcula a média apenas quando a métrica é aplicável."""
    values = [float(row[field]) for row in rows if row[field] != ""]
    return mean(values) if values else None


def summarize(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """Resume as notas e a taxa de alucinação dos quatro cenários."""
    result = []
    for scenario in SCENARIOS:
        selected = [row for row in rows if row["scenario"] == scenario]
        if len(selected) != 10:
            raise ValueError(f"{scenario} deve possuir 10 julgamentos")
        result.append(
            {
                "scenario": scenario,
                "scenario_label": LABELS[scenario],
                "evaluated_cases": len(selected),
                "mean_relevance": average(selected, "judge_relevance_1_5"),
                "mean_correctness": average(selected, "judge_correctness_1_5"),
                "mean_completeness": average(selected, "judge_completeness_1_5"),
                "mean_groundedness": average(selected, "judge_groundedness_1_5"),
                "hallucination_count": sum(
                    row["judge_hallucination_observed"] == "yes"
                    for row in selected
                ),
                "hallucination_rate": sum(
                    row["judge_hallucination_observed"] == "yes"
                    for row in selected
                ) / len(selected),
            }
        )
    return result


def load_successful_jsonl(path: Path) -> dict[str, dict[str, object]]:
    """Carrega o último resultado bem-sucedido de cada chave."""
    results = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("status") == "success":
            results[str(item["judgment_key"])] = item
    return results


def build_agreement() -> list[dict[str, object]]:
    """Compara Qwen e Gemini somente nas chaves avaliadas por ambos."""
    qwen = load_successful_jsonl(
        EVIDENCE_DIR / "automatic_judgments_qwen2_5_7b_instruct.jsonl"
    )
    google = load_successful_jsonl(EVIDENCE_DIR / "automatic_judgments.jsonl")
    rows = []
    for scenario in SCENARIOS:
        keys = sorted(
            key for key in qwen.keys() & google.keys()
            if key.startswith(f"{scenario}::")
        )
        differences = []
        hallucination_matches = 0
        for key in keys:
            fields = ["relevance", "correctness", "completeness"]
            if qwen[key].get("groundedness") is not None and google[key].get("groundedness") is not None:
                fields.append("groundedness")
            differences.extend(
                abs(float(qwen[key][field]) - float(google[key][field]))
                for field in fields
            )
            hallucination_matches += (
                qwen[key]["hallucination_observed"]
                == google[key]["hallucination_observed"]
            )
        rows.append(
            {
                "scenario": scenario,
                "overlapping_cases": len(keys),
                "mean_absolute_score_difference": (
                    mean(differences) if differences else None
                ),
                "hallucination_agreement_rate": (
                    hallucination_matches / len(keys) if keys else None
                ),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Grava CSV com separador compatível com Excel em português."""
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: object) -> str:
    """Formata notas opcionais para a tabela Markdown."""
    return "N/A" if value is None else f"{float(value):.2f}"


def write_report(
    summary: list[dict[str, object]],
    agreement: list[dict[str, object]],
) -> None:
    """Documenta resultados finais e limitações metodológicas."""
    lines = [
        "| Cenário | Relevância | Correção | Completude | Groundedness | Alucinações |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['scenario_label']} | {fmt(row['mean_relevance'])} | "
            f"{fmt(row['mean_correctness'])} | {fmt(row['mean_completeness'])} | "
            f"{fmt(row['mean_groundedness'])} | "
            f"{row['hallucination_count']}/10 ({float(row['hallucination_rate']):.0%}) |"
        )
    overlap = sum(int(row["overlapping_cases"]) for row in agreement)
    differences = [
        float(row["mean_absolute_score_difference"])
        for row in agreement if row["mean_absolute_score_difference"] is not None
    ]
    weighted_difference = sum(
        float(row["mean_absolute_score_difference"]) * int(row["overlapping_cases"])
        for row in agreement if row["mean_absolute_score_difference"] is not None
    ) / overlap
    hallucination_agreement = sum(
        float(row["hallucination_agreement_rate"]) * int(row["overlapping_cases"])
        for row in agreement if row["hallucination_agreement_rate"] is not None
    ) / overlap
    best = summary[-1]
    REPORT_PATH.write_text(
        f"""# Dia 12 — Análise final da avaliação comparativa

**Escopo:** 200 execuções determinísticas e 40 julgamentos qualitativos.  
**Avaliador principal:** `qwen2.5:7b-instruct`, executado localmente pelo Ollama.  
**Estado:** avaliação automática concluída; não constitui avaliação médica humana.

## Notas qualitativas por cenário

{chr(10).join(lines)}

![Notas qualitativas por cenário](figures/evaluation_judge_scores_final.svg)

![Groundedness nos cenários com RAG](figures/evaluation_groundedness_final.svg)

![Alucinações observadas](figures/evaluation_hallucination_final.svg)

## Resultado principal

O cenário ajustado com RAG apresentou as maiores médias: relevância {float(best['mean_relevance']):.2f}, correção {float(best['mean_correctness']):.2f}, completude {float(best['mean_completeness']):.2f} e groundedness {float(best['mean_groundedness']):.2f}. Apenas {best['hallucination_count']} dos 10 casos amostrados foi marcado com possível alucinação. Os dois cenários sem RAG tiveram nove marcações em dez casos cada.

Esse resultado é consistente com as métricas determinísticas anteriores, mas demonstra associação no conjunto avaliado, não eficácia clínica ou causalidade isolada.

## Verificação complementar com Gemini

O arquivo preservado do Gemini contém {overlap} julgamentos também avaliados pelo Qwen. Nesse subconjunto, a diferença absoluta média agregada entre notas foi {weighted_difference:.3f} ponto e a concordância na indicação de alucinação foi {hallucination_agreement:.1%}. A tabela detalhada está em `reports/evidence/evaluation_judge_agreement.csv`.

## Resultados negativos e limitações

- O cenário base com RAG manteve uma falha controlada de geração em `medical_033` nas 200 execuções originais.
- A avaliação qualitativa cobre 10 dos 40 casos médicos de cada cenário, e não todas as 200 linhas.
- O avaliador é uma LLM local; não houve revisão por profissional de saúde.
- As referências e respostas podem estar em idiomas diferentes, afetando métricas lexicais.
- A concordância com Gemini é parcial e não transforma o julgamento em padrão clínico.
- As conclusões se restringem ao conjunto fixo, aos modelos, prompts e hardware registrados.
""",
        encoding="utf-8",
    )


def main() -> int:
    """Gera os artefatos finais e informa os respectivos caminhos."""
    rows = summarize(load_selected_rows())
    agreement = build_agreement()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(SUMMARY_PATH, rows)
    write_csv(AGREEMENT_PATH, agreement)
    write_grouped_chart(
        FIGURES_DIR / "evaluation_judge_scores_final.svg",
        rows,
        (
            ("mean_relevance", "Relevância", "#2563EB"),
            ("mean_correctness", "Correção", "#0F766E"),
            ("mean_completeness", "Completude", "#F59E0B"),
        ),
        "Avaliação qualitativa por cenário",
        "Nota média (1–5)",
        5.0,
    )
    rag_rows = [row for row in rows if row["mean_groundedness"] is not None]
    write_grouped_chart(
        FIGURES_DIR / "evaluation_groundedness_final.svg",
        rag_rows,
        (("mean_groundedness", "Groundedness", "#7C3AED"),),
        "Groundedness nos cenários com RAG",
        "Nota média (1–5)",
        5.0,
    )
    write_grouped_chart(
        FIGURES_DIR / "evaluation_hallucination_final.svg",
        rows,
        (("hallucination_rate", "Taxa de alucinação", "#DC2626"),),
        "Alucinações observadas pelo avaliador",
        "Proporção (0–1)",
        1.0,
    )
    write_report(rows, agreement)
    for path in (SUMMARY_PATH, AGREEMENT_PATH, REPORT_PATH):
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
