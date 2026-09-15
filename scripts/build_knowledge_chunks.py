#!/usr/bin/env python3
"""Converte o MedQuAD curado em documentos e chunks para o pipeline RAG."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "medquad_curated.jsonl"
)

DOCUMENTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "knowledge_documents.jsonl"
)

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "knowledge_chunks.jsonl"
)

MAX_ANSWER_CHARS = 3_500
OVERLAP_CHARS = 300


def stable_document_id(collection: str, xml_path: str) -> str:
    """Gera um identificador reproduzível para o documento original."""
    identity = f"{collection}\x1f{xml_path}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return f"medquad_doc_{digest}"


def split_text(
    text: str,
    max_chars: int = MAX_ANSWER_CHARS,
    overlap_chars: int = OVERLAP_CHARS,
) -> list[str]:
    """Divide respostas extensas em trechos com pequena sobreposição."""
    text = " ".join(text.split())

    if len(text) <= max_chars:
        return [text]

    parts: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + max_chars, len(text))

        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary

        part = text[start:end].strip()

        if part:
            parts.append(part)

        if end >= len(text):
            break

        start = max(end - overlap_chars, start + 1)

        next_space = text.find(" ", start)
        if next_space != -1:
            start = next_space + 1

    return parts


def build_content(
    focus: str,
    question: str,
    answer_part: str,
) -> str:
    """Monta o texto completo que posteriormente será vetorizado."""
    return (
        f"Focus: {focus}\n"
        f"Question: {question}\n"
        f"Answer: {answer_part}"
    )


def load_records(path: Path) -> list[dict[str, Any]]:
    """Carrega os registros JSONL do MedQuAD curado."""
    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"JSON inválido na linha {line_number}: {error}"
                ) from error

    return records


def main() -> None:
    """Cria os arquivos intermediários de documentos e chunks."""
    records = load_records(INPUT_PATH)

    documents: dict[str, dict[str, Any]] = {}
    chunks: list[dict[str, Any]] = []
    document_chunk_indexes: dict[str, int] = {}

    for record in records:
        document_external_id = stable_document_id(
            record["collection"],
            record["xml_path"],
        )

        documents.setdefault(
            document_external_id,
            {
                "external_id": document_external_id,
                "collection": record["collection"],
                "source": record.get("source"),
                "title": record["focus"],
                "url": record.get("url"),
                "metadata": {
                    "source_document_id": record["document_id"],
                    "xml_path": record["xml_path"],
                    "focus_synonyms": record.get(
                        "focus_synonyms",
                        [],
                    ),
                    "umls_cuis": record.get("umls_cuis", []),
                    "semantic_types": record.get(
                        "semantic_types",
                        [],
                    ),
                    "semantic_groups": record.get(
                        "semantic_groups",
                        [],
                    ),
                },
            },
        )

        answer_parts = split_text(record["answer"])

        for part_number, answer_part in enumerate(
            answer_parts,
            start=1,
        ):
            chunk_index = document_chunk_indexes.get(
                document_external_id,
                0,
            )

            chunks.append(
                {
                    "external_id": (
                        f"{record['id']}_part_{part_number:03d}"
                    ),
                    "document_external_id": document_external_id,
                    "chunk_index": chunk_index,
                    "content": build_content(
                        record["focus"],
                        record["question"],
                        answer_part,
                    ),
                    "question": record["question"],
                    "answer": answer_part,
                    "token_count": None,
                    "embedding_model": "embeddinggemma:300m",
                    "metadata": {
                        "medquad_id": record["id"],
                        "question_id": record["question_id"],
                        "pair_id": record["pair_id"],
                        "question_type": record.get(
                            "question_type",
                        ),
                        "part_number": part_number,
                        "total_parts": len(answer_parts),
                    },
                },
            )

            document_chunk_indexes[document_external_id] = (
                chunk_index + 1
            )

    DOCUMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with DOCUMENTS_PATH.open("w", encoding="utf-8") as destination:
        for document in documents.values():
            destination.write(
                json.dumps(document, ensure_ascii=False) + "\n"
            )

    with CHUNKS_PATH.open("w", encoding="utf-8") as destination:
        for chunk in chunks:
            destination.write(
                json.dumps(chunk, ensure_ascii=False) + "\n"
            )

    split_records = sum(
        1
        for chunk in chunks
        if chunk["metadata"]["total_parts"] > 1
    )

    print(f"Registros MedQuAD: {len(records)}")
    print(f"Documentos criados: {len(documents)}")
    print(f"Chunks criados: {len(chunks)}")
    print(f"Chunks provenientes de respostas divididas: {split_records}")
    print(f"Documentos salvos em: {DOCUMENTS_PATH}")
    print(f"Chunks salvos em: {CHUNKS_PATH}")


if __name__ == "__main__":
    main()