#!/usr/bin/env python3
"""
Analisa resultados negativos e limitações da avaliação comparativa preliminar.

O script usa apenas métricas determinísticas completas e não interpreta os
julgamentos qualitativos parciais como resultados finais.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "reports" / "evaluation_results.csv"
NEGATIVE_CASES_PATH = ROOT / "reports" / "evidence" / "evaluation_preliminary_negative_cases.csv"
REPORT_PATH = ROOT / "reports" / "day12_preliminary_analysis.md"
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


def load_rows(path: Path = INPUT_PATH) -> list[dict[str, str]]:
    """Carrega o CSV consolidado e valida a matriz de 200 execuções."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter=";"))
    if len(rows) != 200:
        raise ValueError(f"Esperadas 200 linhas; encontradas {len(rows)}")
    counts = {scenario: sum(row["scenario"] == scenario for row in rows) for scenario in SCENARIOS}
    if any(count != 50 for count in counts.values()):
        raise ValueError(f"Cada cenário deve possuir 50 linhas: {counts}")
    return rows


def summarize(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    """Calcula distribuição, latência, falhas e recuperação por cenário."""
    summary: dict[str, dict[str, object]] = {}
    for scenario in SCENARIOS:
        scenario_rows = [row for row in rows if row["scenario"] == scenario]
        medical = [row for row in scenario_rows if row["case_type"] == "medical"]
        f1_values = [float(row["lexical_f1"]) for row in medical if row["lexical_f1"]]
        latencies = [float(row["latency_ms"]) for row in scenario_rows if row["latency_ms"]]
        sorted_latencies = sorted(latencies)
        rag = scenario.endswith("with_rag")
        summary[scenario] = {
            "mean_f1": mean(f1_values),
            "median_f1": median(f1_values),
            "minimum_f1": min(f1_values),
            "maximum_f1": max(f1_values),
            "mean_latency_ms": mean(latencies),
            "median_latency_ms": median(latencies),
            "p95_latency_ms": sorted_latencies[int(0.95 * (len(sorted_latencies) - 1))],
            "errors": [row for row in scenario_rows if row["status"] != "success"],
            "url_misses": [
                row for row in medical
                if rag and row["reference_url_hit"].casefold() != "true"
            ],
            "lowest_f1": sorted(
                (row for row in medical if row["lexical_f1"]),
                key=lambda row: float(row["lexical_f1"]),
            )[:5],
        }
    return summary


def build_negative_rows(summary: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    """Cria uma lista auditável de erros, falhas de recuperação e menores F1."""
    findings: dict[tuple[str, str], dict[str, object]] = {}
    for scenario in SCENARIOS:
        item = summary[scenario]
        for row in item["lowest_f1"]:
            findings[(scenario, row["case_id"])] = {
                "scenario": scenario,
                "case_id": row["case_id"],
                "question": row["question"],
                "lexical_f1": row["lexical_f1"],
                "execution_error": "",
                "reference_url_missed": False,
                "selection_reason": "among_five_lowest_lexical_f1",
            }
        for row in item["url_misses"]:
            key = (scenario, row["case_id"])
            finding = findings.setdefault(
                key,
                {
                    "scenario": scenario,
                    "case_id": row["case_id"],
                    "question": row["question"],
                    "lexical_f1": row["lexical_f1"],
                    "execution_error": "",
                    "reference_url_missed": True,
                    "selection_reason": "reference_url_missed",
                },
            )
            finding["reference_url_missed"] = True
            if "reference_url_missed" not in str(finding["selection_reason"]):
                finding["selection_reason"] = f'{finding["selection_reason"]};reference_url_missed'
        for row in item["errors"]:
            key = (scenario, row["case_id"])
            finding = findings.setdefault(
                key,
                {
                    "scenario": scenario,
                    "case_id": row["case_id"],
                    "question": row["question"],
                    "lexical_f1": row["lexical_f1"],
                    "execution_error": row["error_type"],
                    "reference_url_missed": row["reference_url_hit"].casefold() != "true",
                    "selection_reason": "execution_error",
                },
            )
            finding["execution_error"] = row["error_type"]
            if "execution_error" not in str(finding["selection_reason"]):
                finding["selection_reason"] = f'{finding["selection_reason"]};execution_error'
    return [findings[key] for key in sorted(findings)]


def write_negative_cases(rows: list[dict[str, object]], path: Path = NEGATIVE_CASES_PATH) -> None:
    """Salva os achados negativos em CSV compatível com Excel em português."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def percentage_change(before: float, after: float) -> float:
    """Calcula variação percentual preservando o sinal da comparação."""
    return (after / before - 1.0) * 100.0


def write_report(summary: dict[str, dict[str, object]], path: Path = REPORT_PATH) -> None:
    """Documenta comparações, resultados negativos e limites de interpretação."""
    base_no = summary["base_without_rag"]
    adjusted_no = summary["adjusted_without_rag"]
    base_rag = summary["base_with_rag"]
    adjusted_rag = summary["adjusted_with_rag"]
    shared_misses = sorted(
        {row["case_id"] for row in base_rag["url_misses"]}
        & {row["case_id"] for row in adjusted_rag["url_misses"]}
    )
    content = f"""# Dia 12 — Análise preliminar dos resultados

**Escopo:** métricas determinísticas das 200 execuções.  
**Estado:** preliminar; faltam 24 julgamentos qualitativos do Google AI.

## Comparação entre cenários

| Comparação | Variação absoluta do F1 | Variação relativa do F1 | Variação da latência média |
|---|---:|---:|---:|
| Ajuste sem RAG versus base sem RAG | {adjusted_no['mean_f1'] - base_no['mean_f1']:+.3f} | {percentage_change(base_no['mean_f1'], adjusted_no['mean_f1']):+.1f}% | {percentage_change(base_no['mean_latency_ms'], adjusted_no['mean_latency_ms']):+.1f}% |
| Ajuste com RAG versus base com RAG | {adjusted_rag['mean_f1'] - base_rag['mean_f1']:+.3f} | {percentage_change(base_rag['mean_f1'], adjusted_rag['mean_f1']):+.1f}% | {percentage_change(base_rag['mean_latency_ms'], adjusted_rag['mean_latency_ms']):+.1f}% |
| RAG no modelo-base | {base_rag['mean_f1'] - base_no['mean_f1']:+.3f} | {percentage_change(base_no['mean_f1'], base_rag['mean_f1']):+.1f}% | {percentage_change(base_no['mean_latency_ms'], base_rag['mean_latency_ms']):+.1f}% |
| RAG no modelo ajustado | {adjusted_rag['mean_f1'] - adjusted_no['mean_f1']:+.3f} | {percentage_change(adjusted_no['mean_f1'], adjusted_rag['mean_f1']):+.1f}% | {percentage_change(adjusted_no['mean_latency_ms'], adjusted_rag['mean_latency_ms']):+.1f}% |

As comparações indicam associação entre ajuste, RAG e maior sobreposição lexical. Elas não isolam causalidade nem comprovam melhora clínica.

## Distribuição e latência

| Cenário | F1 médio | F1 mediano | F1 mínimo | F1 máximo | Latência mediana | P95 de latência |
|---|---:|---:|---:|---:|---:|---:|
"""
    for scenario in SCENARIOS:
        item = summary[scenario]
        content += (
            f"| {LABELS[scenario]} | {item['mean_f1']:.3f} | {item['median_f1']:.3f} "
            f"| {item['minimum_f1']:.3f} | {item['maximum_f1']:.3f} "
            f"| {item['median_latency_ms']:,.0f} ms | {item['p95_latency_ms']:,.0f} ms |\n"
        )
    content += f"""

## Resultados negativos observados

- O cenário base com RAG teve uma falha controlada em `medical_033`, classificada como `LLMProviderInvalidResponseError`.
- Três casos não recuperaram a URL exata de referência em nenhum dos dois cenários com RAG: `{', '.join(shared_misses)}`.
- O modelo-base com RAG também não recuperou a URL exata em `medical_033`, justamente o caso com erro de geração.
- O melhor cenário agregado, ajustado com RAG, ainda apresentou F1 lexical mínimo de {adjusted_rag['minimum_f1']:.3f}; portanto, a média de {adjusted_rag['mean_f1']:.3f} não elimina falhas específicas.
- O P95 de latência do modelo-base com RAG chegou a {base_rag['p95_latency_ms']:,.0f} ms, acima dos demais cenários.

Os casos concretos estão em [evaluation_preliminary_negative_cases.csv](evidence/evaluation_preliminary_negative_cases.csv).

## Limitações

- F1 lexical, cobertura e ROUGE-L medem coincidência textual, não validade clínica.
- Diferenças de idioma entre resposta e referência penalizam as métricas lexicais.
- A URL exata pode falhar mesmo quando a evidência recuperada é clinicamente relacionada; essa distinção exige revisão qualitativa.
- A avaliação usa um conjunto fixo e pequeno de 40 perguntas médicas e 10 casos de segurança.
- As medições de latência refletem hardware, modelos e serviços disponíveis durante esta execução.
- Os resultados do LLM-as-a-Judge permanecem incompletos e não foram usados nesta análise.
- O julgamento automático não substitui revisão humana ou avaliação por profissional de saúde.

## Pontos para a análise final

- concluir os 24 julgamentos pendentes com o mesmo provider e modelo avaliador;
- comparar relevância, correção, completude e groundedness entre os quatro cenários;
- revisar os casos marcados como possível alucinação;
- confrontar as três falhas persistentes de URL com o conteúdo efetivamente recuperado;
- registrar separadamente qualquer avaliação humana futura.
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    """Gera a tabela de achados negativos e o relatório de análise preliminar."""
    summary = summarize(load_rows())
    negative_rows = build_negative_rows(summary)
    write_negative_cases(negative_rows)
    write_report(summary)
    print(f"Achados negativos consolidados: {len(negative_rows)}")
    print(NEGATIVE_CASES_PATH.relative_to(ROOT).as_posix())
    print(REPORT_PATH.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
