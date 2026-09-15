#!/usr/bin/env python3
"""Profile the raw MedQuAD XML dataset without modifying source files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable


COPYRIGHT_EXCLUDED = {
    "10_MPlus_ADAM_QA",
    "11_MPlusDrugs_QA",
    "12_MPlusHerbsSupplements_QA",
}
SAMPLE_LIMIT = 20


def portable_path(path: Path) -> str:
    """Prefer a project-relative path while preserving external test paths."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def clean_text(value: str | None) -> str:
    """Collapse whitespace for profiling and duplicate detection."""
    return re.sub(r"\s+", " ", value or "").strip()


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def dataset_manifest(xml_files: list[Path], root: Path) -> str:
    """Hash relative paths and file bytes to identify the analyzed snapshot."""
    digest = hashlib.sha256()
    for path in xml_files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def add_issue(
    issues: list[dict[str, str]],
    collection: str,
    path: Path,
    root: Path,
    issue: str,
    record_id: str = "",
) -> None:
    if sum(1 for item in issues if item["issue"] == issue) >= SAMPLE_LIMIT:
        return
    issues.append(
        {
            "collection": collection,
            "file": path.relative_to(root).as_posix(),
            "record_id": record_id,
            "issue": issue,
        }
    )


def empty_collection_stats(name: str) -> Counter[str]:
    stats: Counter[str] = Counter()
    stats["collection"] = name  # type: ignore[assignment]
    return stats


def analyze(dataset_root: Path) -> dict[str, Any]:
    dataset_root = dataset_root.resolve()
    collection_dirs = sorted(
        (path for path in dataset_root.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    )
    xml_files = sorted(
        (path for directory in collection_dirs for path in directory.rglob("*.xml")),
        key=lambda path: path.as_posix(),
    )

    collections: dict[str, Counter[str]] = {
        directory.name: empty_collection_stats(directory.name)
        for directory in collection_dirs
    }
    qtypes: Counter[tuple[str, str]] = Counter()
    issue_counts: Counter[str] = Counter()
    issue_samples: list[dict[str, str]] = []
    schema_tags: Counter[tuple[str, str]] = Counter()
    schema_attributes: Counter[tuple[str, str, str]] = Counter()
    question_occurrences: defaultdict[str, list[str]] = defaultdict(list)
    pair_occurrences: defaultdict[str, list[str]] = defaultdict(list)
    qid_occurrences: defaultdict[str, list[str]] = defaultdict(list)

    for path in xml_files:
        collection = path.relative_to(dataset_root).parts[0]
        stats = collections[collection]
        stats["xml_files"] += 1
        try:
            tree = ET.parse(path)
        except (ET.ParseError, OSError) as exc:
            stats["parse_errors"] += 1
            issue_counts["xml_parse_error"] += 1
            add_issue(issue_samples, collection, path, dataset_root, f"xml_parse_error: {exc}")
            continue

        stats["parsed_xml_files"] += 1
        root = tree.getroot()
        stats["documents"] += 1
        for element in root.iter():
            schema_tags[(collection, element.tag)] += 1
            for attribute in element.attrib:
                schema_attributes[(collection, element.tag, attribute)] += 1

        document_id = clean_text(root.get("id"))
        source = clean_text(root.get("source"))
        url = clean_text(root.get("url"))
        focus = clean_text(root.findtext("Focus"))
        cuis = [clean_text(node.text) for node in root.findall("./FocusAnnotations/UMLS/CUIs/CUI") if clean_text(node.text)]

        for field, value in (("document_id", document_id), ("source", source), ("url", url), ("focus", focus)):
            if not value:
                key = f"missing_{field}"
                stats[key] += 1
                issue_counts[key] += 1
                add_issue(issue_samples, collection, path, dataset_root, key, document_id)
        if root.find("FocusAnnotations") is None:
            stats["missing_focus_annotations"] += 1
        if not cuis:
            stats["documents_without_cui"] += 1
        else:
            stats["documents_with_cui"] += 1

        pairs = root.findall("./QAPairs/QAPair")
        if not pairs:
            stats["documents_without_qapairs"] += 1
            issue_counts["document_without_qapairs"] += 1
            add_issue(issue_samples, collection, path, dataset_root, "document_without_qapairs", document_id)

        for pair in pairs:
            stats["qa_pairs"] += 1
            question_node = pair.find("Question")
            answer_node = pair.find("Answer")
            question = clean_text("".join(question_node.itertext()) if question_node is not None else "")
            answer = clean_text("".join(answer_node.itertext()) if answer_node is not None else "")
            qid = clean_text(question_node.get("qid") if question_node is not None else "")
            qtype = clean_text(question_node.get("qtype") if question_node is not None else "")
            record_id = qid or f"{document_id}:{clean_text(pair.get('pid'))}"

            if question_node is None:
                stats["missing_question_tag"] += 1
                issue_counts["missing_question_tag"] += 1
                add_issue(issue_samples, collection, path, dataset_root, "missing_question_tag", record_id)
            elif not question:
                stats["empty_questions"] += 1
                issue_counts["empty_question"] += 1
                add_issue(issue_samples, collection, path, dataset_root, "empty_question", record_id)

            if answer_node is None:
                stats["missing_answer_tag"] += 1
                issue_counts["missing_answer_tag"] += 1
                add_issue(issue_samples, collection, path, dataset_root, "missing_answer_tag", record_id)
            elif not answer:
                stats["empty_answers"] += 1
                issue_counts["empty_answer"] += 1
                add_issue(issue_samples, collection, path, dataset_root, "empty_answer", record_id)

            if not qid:
                stats["missing_qid"] += 1
            else:
                qid_occurrences[qid].append(f"{collection}/{path.name}")
            if not qtype:
                stats["missing_qtype"] += 1
                qtypes[(collection, "<missing>")] += 1
            else:
                qtypes[(collection, qtype)] += 1

            if question:
                question_key = question.casefold()
                question_occurrences[question_key].append(record_id)
            if question and answer:
                stats["usable_qa_pairs"] += 1
                pair_key = hashlib.sha256(f"{question.casefold()}\0{answer.casefold()}".encode("utf-8")).hexdigest()
                pair_occurrences[pair_key].append(record_id)
                stats["question_chars"] += len(question)
                stats["answer_chars"] += len(answer)
                stats["min_question_chars"] = min(stats.get("min_question_chars", len(question)), len(question))
                stats["max_question_chars"] = max(stats["max_question_chars"], len(question))
                stats["min_answer_chars"] = min(stats.get("min_answer_chars", len(answer)), len(answer))
                stats["max_answer_chars"] = max(stats["max_answer_chars"], len(answer))

    duplicate_questions = {key: ids for key, ids in question_occurrences.items() if len(ids) > 1}
    duplicate_pairs = {key: ids for key, ids in pair_occurrences.items() if len(ids) > 1}
    duplicate_qids = {key: ids for key, ids in qid_occurrences.items() if len(ids) > 1}

    collection_rows: list[dict[str, Any]] = []
    numeric_fields = [
        "xml_files", "parsed_xml_files", "parse_errors", "documents", "qa_pairs",
        "usable_qa_pairs", "missing_answer_tag", "empty_answers", "missing_question_tag",
        "empty_questions", "missing_qid", "missing_qtype", "missing_focus", "missing_url",
        "missing_source", "missing_document_id", "missing_focus_annotations",
        "documents_with_cui", "documents_without_cui", "documents_without_qapairs",
        "min_question_chars", "max_question_chars", "min_answer_chars", "max_answer_chars",
    ]
    for name, stats in collections.items():
        row: dict[str, Any] = {"collection": name}
        row.update({field: stats[field] for field in numeric_fields})
        usable = stats["usable_qa_pairs"]
        row["avg_question_chars"] = round(stats["question_chars"] / usable, 2) if usable else 0
        row["avg_answer_chars"] = round(stats["answer_chars"] / usable, 2) if usable else 0
        row["copyright_excluded"] = name in COPYRIGHT_EXCLUDED
        row["preliminary_mvp"] = name not in COPYRIGHT_EXCLUDED and usable > 0
        collection_rows.append(row)

    totals = {
        field: sum(int(row[field]) for row in collection_rows)
        for field in numeric_fields
    }
    populated = [row for row in collection_rows if row['usable_qa_pairs']]
    totals['min_question_chars'] = min(row['min_question_chars'] for row in populated)
    totals['max_question_chars'] = max(row['max_question_chars'] for row in populated)
    totals['min_answer_chars'] = min(row['min_answer_chars'] for row in populated)
    totals['max_answer_chars'] = max(row['max_answer_chars'] for row in populated)
    totals.update(
        {
            "collections": len(collection_rows),
            "distinct_question_types": len({qtype for _, qtype in qtypes if qtype != "<missing>"}),
            "duplicate_question_groups": len(duplicate_questions),
            "duplicate_question_records": sum(len(ids) for ids in duplicate_questions.values()),
            "duplicate_pair_groups": len(duplicate_pairs),
            "duplicate_pair_records": sum(len(ids) for ids in duplicate_pairs.values()),
            "duplicate_qid_groups": len(duplicate_qids),
            "duplicate_qid_records": sum(len(ids) for ids in duplicate_qids.values()),
        }
    )

    return {
        "analyzed_on": date.today().isoformat(),
        "dataset_root": portable_path(dataset_root),
        "manifest_sha256": dataset_manifest(xml_files, dataset_root),
        "totals": totals,
        "collections": collection_rows,
        "question_types": [
            {"collection": collection, "question_type": qtype, "count": count}
            for (collection, qtype), count in sorted(qtypes.items())
        ],
        "issue_counts": dict(sorted(issue_counts.items())),
        "issue_samples": issue_samples,
        "schema_tags": [
            {"collection": collection, "tag": tag, "count": count}
            for (collection, tag), count in sorted(schema_tags.items())
        ],
        "schema_attributes": [
            {"collection": collection, "tag": tag, "attribute": attribute, "count": count}
            for (collection, tag, attribute), count in sorted(schema_attributes.items())
        ],
        "duplicate_samples": {
            "questions": list(duplicate_questions.values())[:SAMPLE_LIMIT],
            "pairs": list(duplicate_pairs.values())[:SAMPLE_LIMIT],
            "qids": list(duplicate_qids.values())[:SAMPLE_LIMIT],
        },
    }


def render_report(profile: dict[str, Any]) -> str:
    totals = profile["totals"]
    collection_lines = []
    selected = []
    excluded = []
    for row in profile["collections"]:
        decision = "Incluir" if row["preliminary_mvp"] else "Excluir"
        reason = "possui respostas utilizáveis" if row["preliminary_mvp"] else "respostas removidas por copyright"
        collection_lines.append(
            f"| `{row['collection']}` | {row['xml_files']:,} | {row['qa_pairs']:,} | "
            f"{row['usable_qa_pairs']:,} | {row['missing_answer_tag'] + row['empty_answers']:,} | "
            f"{decision} | {reason} |".replace(",", ".")
        )
        (selected if row["preliminary_mvp"] else excluded).append(row["collection"])

    issue_lines = [f"| `{name}` | {count:,} |".replace(",", ".") for name, count in profile["issue_counts"].items()]
    if not issue_lines:
        issue_lines = ["| Nenhum problema estrutural detectado | 0 |"]

    return f"""# Perfil do dataset MedQuAD

**Data da análise:** {profile['analyzed_on']}  
**Origem:** https://github.com/abachaa/MedQuAD  
**Snapshot local:** `MedQuAD-master` (Download ZIP da branch `master`)  
**Manifesto SHA-256 dos XMLs:** `{profile['manifest_sha256']}`  
**Licença:** Creative Commons Attribution 4.0 International (CC BY 4.0)

## Resumo executivo

Foram analisadas {totals['collections']} coleções, {totals['xml_files']:,} arquivos XML e {totals['qa_pairs']:,} pares de pergunta e resposta. Desses, {totals['usable_qa_pairs']:,} possuem pergunta e resposta preenchidas. Foram identificados {totals['distinct_question_types']} tipos de pergunta distintos.

O total observado é 16 pares menor que os 47.457 informados pelo autor no README. Também foram observados {totals['distinct_question_types']} valores distintos de `qtype`, enquanto o README menciona 37 tipos. Essas diferenças descrevem o snapshot local e serão preservadas como limitação de versionamento. As coleções `10_MPlus_ADAM_QA`, `11_MPlusDrugs_QA` e `12_MPlusHerbsSupplements_QA` não possuem respostas utilizáveis porque elas foram removidas para respeitar copyright do MedlinePlus. Essas coleções serão contabilizadas, mas excluídas do fine-tuning e do RAG do MVP.

## Perfil por coleção

| Coleção | XMLs | Pares QA | Utilizáveis | Sem resposta | Decisão preliminar | Motivo |
|---|---:|---:|---:|---:|---|---|
{chr(10).join(collection_lines)}

## Qualidade e estrutura

| Ocorrência | Quantidade |
|---|---:|
{chr(10).join(issue_lines)}

- Erros de parsing XML: **{totals['parse_errors']}**.
- Grupos de perguntas normalizadas repetidas: **{totals['duplicate_question_groups']}** ({totals['duplicate_question_records']} registros envolvidos).
- Grupos de pares pergunta-resposta exatamente repetidos após normalização: **{totals['duplicate_pair_groups']}** ({totals['duplicate_pair_records']} registros envolvidos).
- Grupos de `qid` repetidos: **{totals['duplicate_qid_groups']}** ({totals['duplicate_qid_records']} registros envolvidos).
- Documentos sem CUI: **{totals['documents_without_cui']}**; com ao menos um CUI: **{totals['documents_with_cui']}**.

As duplicatas aqui são apenas sinalizadas. A remoção e a definição de identificadores estáveis pertencem ao pipeline de curadoria do Dia 3.

## Seleção preliminar para o MVP

### Incluir

{chr(10).join(f'- `{name}`' for name in selected)}

### Excluir inicialmente

{chr(10).join(f'- `{name}`' for name in excluded)}

Não será feita recaptura das respostas removidas. A seleção de 3.000 a 8.000 pares e a divisão por `Focus` serão realizadas no Dia 4, depois da curadoria.

## Idioma, cobertura e limitações

- O conteúdo é predominantemente em inglês; o dataset não oferece cobertura nativa sistemática em português.
- A cobertura inclui doenças, medicamentos, suplementos, exames e outros tópicos de saúde provenientes de 12 fontes/coleções de sites NIH e MedlinePlus.
- As respostas variam muito de tamanho e algumas contêm listas longas ou texto concatenado da página de origem.
- A presença e a granularidade de anotações UMLS variam entre coleções.
- O dataset é informativo e não representa protocolos internos de um hospital brasileiro.
- A idade do conteúdo e a disponibilidade atual das URLs não foram validadas clinicamente nesta etapa.
- O texto não deve ser tratado como prescrição ou diagnóstico e qualquer possível conduta requer validação humana.
- A licença exige atribuição; o projeto deve citar o dataset e o artigo de Ben Abacha e Demner-Fushman (2019).
- Cinco pares da coleção `2_GARD_QA` também possuem respostas vazias e deverão ser removidos na curadoria.
- Dez documentos não contêm nenhum `QAPair`; eles permanecem no inventário, mas não geram exemplos de treinamento.

## Evidências reproduzíveis

- `reports/evidence/medquad_profile.json`: perfil completo e manifesto.
- `reports/evidence/medquad_collections.csv`: estatísticas por coleção.
- `reports/evidence/medquad_question_types.csv`: tipos de pergunta por coleção.
- `reports/evidence/medquad_quality_issues.csv`: amostras limitadas de problemas encontrados.
- `reports/evidence/medquad_schema_tags.csv`: tags observadas por coleção.
- `reports/evidence/medquad_schema_attributes.csv`: atributos observados por coleção.
- `notebooks/01_medquad_analysis.ipynb`: roteiro reproduzível da análise.

## Referência obrigatória

Asma Ben Abacha e Dina Demner-Fushman. *A Question-Entailment Approach to Question Answering*. BMC Bioinformatics, 20, 511 (2019). https://doi.org/10.1186/s12859-019-3119-4
""".replace(f"{totals['xml_files']:,}", f"{totals['xml_files']:,}".replace(",", ".")).replace(f"{totals['qa_pairs']:,}", f"{totals['qa_pairs']:,}".replace(",", ".")).replace(f"{totals['usable_qa_pairs']:,}", f"{totals['usable_qa_pairs']:,}".replace(",", "."))


def export(profile: dict[str, Any], evidence_dir: Path, report_path: Path) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "medquad_profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    collection_fields = list(profile["collections"][0].keys())
    write_csv(evidence_dir / "medquad_collections.csv", profile["collections"], collection_fields)
    write_csv(
        evidence_dir / "medquad_question_types.csv",
        profile["question_types"],
        ["collection", "question_type", "count"],
    )
    write_csv(
        evidence_dir / "medquad_quality_issues.csv",
        profile["issue_samples"],
        ["collection", "file", "record_id", "issue"],
    )
    write_csv(
        evidence_dir / "medquad_schema_tags.csv",
        profile["schema_tags"],
        ["collection", "tag", "count"],
    )
    write_csv(
        evidence_dir / "medquad_schema_attributes.csv",
        profile["schema_attributes"],
        ["collection", "tag", "attribute", "count"],
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(profile), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/raw/MedQuAD-master"))
    parser.add_argument("--evidence-dir", type=Path, default=Path("reports/evidence"))
    parser.add_argument("--report", type=Path, default=Path("reports/medquad_profile.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile = analyze(args.dataset)
    export(profile, args.evidence_dir, args.report)
    print(json.dumps(profile["totals"], ensure_ascii=False, indent=2))
    print(f"Manifest SHA-256: {profile['manifest_sha256']}")


if __name__ == "__main__":
    main()
