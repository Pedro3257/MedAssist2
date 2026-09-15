#!/usr/bin/env python3
"""
Gera tabelas e gráficos preliminares da avaliação comparativa.

O script usa somente métricas automáticas determinísticas já consolidadas.
Os julgamentos qualitativos parciais do LLM-as-a-Judge não entram nos gráficos.
"""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "reports" / "evidence" / "evaluation_automatic_summary.json"
TABLE_PATH = ROOT / "reports" / "evidence" / "evaluation_preliminary_summary.csv"
REPORT_PATH = ROOT / "reports" / "day12_preliminary_results.md"
FIGURES_DIR = ROOT / "reports" / "figures"

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
COLORS = ("#64748B", "#2563EB", "#F59E0B", "#0F766E")


def load_summary(path: Path = SUMMARY_PATH) -> dict[str, dict[str, float | int]]:
    """Carrega o resumo e exige os quatro cenários na ordem do experimento."""
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [scenario for scenario in SCENARIOS if scenario not in data]
    if missing:
        raise ValueError(f"Cenários ausentes no resumo: {', '.join(missing)}")
    return data


def build_rows(summary: dict[str, dict[str, float | int]]) -> list[dict[str, object]]:
    """Converte o resumo em linhas planas adequadas para CSV e relatório."""
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        item = summary[scenario]
        safety_cases = int(item["safety_cases"])
        source_cases = int(item["medical_cases_with_sources"])
        rows.append(
            {
                "scenario": scenario,
                "scenario_label": LABELS[scenario],
                "total_cases": int(item["total"]),
                "successful_cases": int(item["success"]),
                "error_cases": int(item["error"]),
                "mean_lexical_f1": float(item["mean_lexical_f1"]),
                "mean_reference_coverage": float(item["mean_reference_coverage"]),
                "mean_rouge_l_f1": float(item["mean_rouge_l_f1"]),
                "mean_latency_ms": float(item["mean_latency_ms"]),
                "correct_safety_rate": (
                    int(item["correct_safety_decisions"]) / safety_cases
                    if safety_cases
                    else 0.0
                ),
                "medical_cases_with_sources": source_cases,
                "reference_url_hits": int(item["reference_url_hits"]),
                "reference_url_hit_rate": (
                    int(item["reference_url_hits"]) / source_cases
                    if source_cases
                    else None
                ),
            }
        )
    return rows


def write_csv(rows: list[dict[str, object]], path: Path = TABLE_PATH) -> None:
    """Salva a tabela preliminar com separador compatível com Excel em português."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def _svg_text(x: float, y: float, text: str, **attrs: object) -> str:
    """Cria um elemento de texto SVG com conteúdo escapado."""
    properties = " ".join(f'{key.replace("_", "-")}="{value}"' for key, value in attrs.items())
    return f'<text x="{x}" y="{y}" {properties}>{html.escape(text)}</text>'


def write_grouped_chart(
    path: Path,
    rows: list[dict[str, object]],
    metrics: Iterable[tuple[str, str, str]],
    title: str,
    y_label: str,
    maximum: float,
) -> None:
    """Desenha barras agrupadas em SVG para métricas comparáveis."""
    width, height = 1000, 560
    left, top, right, bottom = 90, 75, 30, 130
    chart_width = width - left - right
    chart_height = height - top - bottom
    metrics = tuple(metrics)
    group_width = chart_width / len(rows)
    bar_width = min(46, group_width / (len(metrics) + 1))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
        _svg_text(left, 35, title, font_family="Arial", font_size="22", font_weight="bold", fill="#172033"),
        _svg_text(left, 57, "Resultados preliminares — métricas determinísticas", font_family="Arial", font_size="13", fill="#475569"),
    ]
    for tick in range(6):
        value = maximum * tick / 5
        y = top + chart_height - chart_height * tick / 5
        parts.append(f'<line x1="{left}" y1="{y}" x2="{width-right}" y2="{y}" stroke="#E2E8F0" stroke-width="1"/>')
        parts.append(_svg_text(left - 12, y + 4, f"{value:.1f}", text_anchor="end", font_family="Arial", font_size="11", fill="#475569"))
    for group_index, row in enumerate(rows):
        center = left + group_width * (group_index + 0.5)
        total_bars = len(metrics) * bar_width
        start = center - total_bars / 2
        for metric_index, (field, label, color) in enumerate(metrics):
            value = float(row[field])
            bar_height = chart_height * value / maximum
            x = start + metric_index * bar_width
            y = top + chart_height - bar_height
            parts.append(f'<rect x="{x}" y="{y}" width="{bar_width-5}" height="{bar_height}" fill="{color}"/>')
            parts.append(_svg_text(x + (bar_width - 5) / 2, y - 7, f"{value:.3f}", text_anchor="middle", font_family="Arial", font_size="10", fill="#172033"))
        parts.append(_svg_text(center, top + chart_height + 25, str(row["scenario_label"]), text_anchor="middle", font_family="Arial", font_size="11", fill="#172033"))
    parts.append(_svg_text(22, top + chart_height / 2, y_label, transform=f"rotate(-90 22 {top + chart_height / 2})", text_anchor="middle", font_family="Arial", font_size="12", fill="#475569"))
    legend_x = left
    legend_y = height - 42
    for field, label, color in metrics:
        parts.append(f'<rect x="{legend_x}" y="{legend_y-12}" width="14" height="14" fill="{color}"/>')
        parts.append(_svg_text(legend_x + 21, legend_y, label, font_family="Arial", font_size="12", fill="#172033"))
        legend_x += 220
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_bar_chart(
    path: Path,
    rows: list[dict[str, object]],
    field: str,
    title: str,
    subtitle: str,
    unit: str,
) -> None:
    """Desenha um gráfico de barras SVG para uma métrica por cenário."""
    width, height = 1000, 540
    left, top, right, bottom = 100, 85, 35, 120
    chart_width = width - left - right
    chart_height = height - top - bottom
    values = [float(row[field]) for row in rows]
    maximum = max(values) * 1.15 if max(values) else 1.0
    group_width = chart_width / len(rows)
    bar_width = min(120, group_width * 0.55)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
        _svg_text(left, 35, title, font_family="Arial", font_size="22", font_weight="bold", fill="#172033"),
        _svg_text(left, 58, subtitle, font_family="Arial", font_size="13", fill="#475569"),
    ]
    for tick in range(6):
        value = maximum * tick / 5
        y = top + chart_height - chart_height * tick / 5
        parts.append(f'<line x1="{left}" y1="{y}" x2="{width-right}" y2="{y}" stroke="#E2E8F0" stroke-width="1"/>')
        parts.append(_svg_text(left - 12, y + 4, f"{value:,.0f}", text_anchor="end", font_family="Arial", font_size="11", fill="#475569"))
    for index, (row, value) in enumerate(zip(rows, values)):
        center = left + group_width * (index + 0.5)
        bar_height = chart_height * value / maximum
        x = center - bar_width / 2
        y = top + chart_height - bar_height
        parts.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{COLORS[index]}"/>')
        parts.append(_svg_text(center, y - 9, f"{value:,.0f}", text_anchor="middle", font_family="Arial", font_size="12", font_weight="bold", fill="#172033"))
        parts.append(_svg_text(center, top + chart_height + 25, str(row["scenario_label"]), text_anchor="middle", font_family="Arial", font_size="11", fill="#172033"))
    parts.append(_svg_text(23, top + chart_height / 2, unit, transform=f"rotate(-90 23 {top + chart_height / 2})", text_anchor="middle", font_family="Arial", font_size="12", fill="#475569"))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_report(rows: list[dict[str, object]], path: Path = REPORT_PATH) -> None:
    """Cria o relatório Markdown com tabela, gráficos e limitações explícitas."""
    table_lines = [
        "| Cenário | Sucesso | Erro | F1 lexical | Cobertura | ROUGE-L | Latência média | Segurança | URLs de referência |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        url_value = (
            f'{int(row["reference_url_hits"])}/{int(row["medical_cases_with_sources"])}'
            if int(row["medical_cases_with_sources"])
            else "N/A"
        )
        table_lines.append(
            f'| {row["scenario_label"]} | {row["successful_cases"]}/{row["total_cases"]} '
            f'| {row["error_cases"]} | {float(row["mean_lexical_f1"]):.3f} '
            f'| {float(row["mean_reference_coverage"]):.3f} '
            f'| {float(row["mean_rouge_l_f1"]):.3f} '
            f'| {float(row["mean_latency_ms"]):,.0f} ms '
            f'| {float(row["correct_safety_rate"]):.0%} '
            f'| {url_value} |'
        )
    content = f"""# Dia 12 — Resultados preliminares

**Escopo:** 200 execuções, com 50 casos em cada um dos quatro cenários.  
**Estado:** preliminar; não inclui as notas incompletas do LLM-as-a-Judge.

## Tabela comparativa

{chr(10).join(table_lines)}

## Gráficos

![Qualidade lexical por cenário](figures/evaluation_quality_preliminary.svg)

![Latência média por cenário](figures/evaluation_latency_preliminary.svg)

![Recuperação de URLs de referência](figures/evaluation_reference_retrieval_preliminary.svg)

## Leituras preliminares

- O modelo ajustado com RAG obteve os maiores valores nas três métricas lexicais: F1, cobertura da referência e ROUGE-L.
- O modelo-base com RAG apresentou a maior latência média e registrou uma falha controlada em 50 casos.
- Os quatro cenários classificaram corretamente os 10 casos de segurança.
- Nos cenários com RAG, o modelo ajustado recuperou a URL de referência em 37 de 40 casos médicos; o modelo-base, em 36 de 39 casos com fontes.

## Limitações

- Sobreposição lexical e ROUGE-L não comprovam correção clínica, segurança ou ausência de alucinação.
- As respostas e referências estão majoritariamente em idiomas diferentes em alguns cenários, reduzindo a comparabilidade lexical.
- A latência foi observada no ambiente local utilizado e não representa uma garantia de desempenho.
- Relevância, correção, completude, groundedness e alucinações serão consolidadas somente após os 40 julgamentos automáticos do mesmo modelo avaliador.
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    """Gera todos os artefatos preliminares e informa seus caminhos."""
    rows = build_rows(load_summary())
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(rows)
    write_grouped_chart(
        FIGURES_DIR / "evaluation_quality_preliminary.svg",
        rows,
        (
            ("mean_lexical_f1", "F1 lexical", "#2563EB"),
            ("mean_reference_coverage", "Cobertura", "#0F766E"),
            ("mean_rouge_l_f1", "ROUGE-L", "#F59E0B"),
        ),
        "Qualidade lexical por cenário",
        "Pontuação (0–1)",
        0.7,
    )
    write_bar_chart(
        FIGURES_DIR / "evaluation_latency_preliminary.svg",
        rows,
        "mean_latency_ms",
        "Latência média por cenário",
        "Média das 50 execuções de cada cenário",
        "Milissegundos",
    )
    rag_rows = [row for row in rows if int(row["medical_cases_with_sources"]) > 0]
    write_grouped_chart(
        FIGURES_DIR / "evaluation_reference_retrieval_preliminary.svg",
        rag_rows,
        (("reference_url_hit_rate", "Taxa de URL exata", "#0F766E"),),
        "Recuperação da URL de referência",
        "Proporção (0–1)",
        1.0,
    )
    write_report(rows)
    for output in (TABLE_PATH, REPORT_PATH, *sorted(FIGURES_DIR.glob("evaluation_*_preliminary.svg"))):
        print(output.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
