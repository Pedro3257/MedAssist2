#!/usr/bin/env python3
'''Create the canonical, model-independent MedQuAD JSONL dataset.'''

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterator


COPYRIGHT_EXCLUDED = {
    '10_MPlus_ADAM_QA',
    '11_MPlusDrugs_QA',
    '12_MPlusHerbsSupplements_QA',
}
DEFAULT_MIN_QUESTION_CHARS = 10
DEFAULT_MAX_QUESTION_CHARS = 500
DEFAULT_MIN_ANSWER_CHARS = 20
DEFAULT_MAX_ANSWER_CHARS = 30_000


def portable_path(path: Path) -> str:
    '''Prefer a project-relative path while preserving external test paths.'''
    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


class _HTMLTextExtractor(HTMLParser):
    '''Collect visible text from escaped HTML fragments.'''

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def normalize_text(value: str | None) -> str:
    '''Decode entities, remove HTML markup and normalize Unicode/whitespace.'''
    text = html.unescape(html.unescape(value or ''))
    if '<' in text and '>' in text:
        parser = _HTMLTextExtractor()
        try:
            parser.feed(text)
            parser.close()
            text = ' '.join(parser.parts)
        except Exception:
            pass
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\u200b', '').replace('\ufeff', '')
    return re.sub(r'\s+', ' ', text).strip()


def element_text(element: ET.Element | None) -> str:
    if element is None:
        return ''
    return normalize_text(' '.join(element.itertext()))


def stable_id(record: dict[str, Any]) -> str:
    '''Create a deterministic ID tied to source identity and normalized content.'''
    identity = '\x1f'.join(
        str(record[field])
        for field in (
            'collection',
            'xml_path',
            'document_id',
            'question_id',
            'question',
            'answer',
        )
    )
    return 'medquad_' + hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]


def _values(root: ET.Element, tag: str) -> list[str]:
    values = {element_text(node) for node in root.findall(f'.//{tag}')}
    return sorted(value for value in values if value)


def iter_candidates(
    dataset_root: Path,
    stats: Counter[str],
) -> Iterator[dict[str, Any]]:
    '''Yield normalized candidates from all non-copyright collections.'''
    dataset_root = dataset_root.resolve()
    collections = sorted(path for path in dataset_root.iterdir() if path.is_dir())
    stats['collections_seen'] = len(collections)

    for collection_dir in collections:
        collection = collection_dir.name
        for path in sorted(collection_dir.rglob('*.xml')):
            stats['xml_files_seen'] += 1
            try:
                root = ET.parse(path).getroot()
            except (ET.ParseError, OSError):
                stats['rejected_xml_parse_error'] += 1
                continue

            pairs = root.findall('./QAPairs/QAPair')
            if collection in COPYRIGHT_EXCLUDED:
                stats['copyright_excluded_xml_files'] += 1
                stats['copyright_excluded_pairs'] += len(pairs)
                continue

            stats['included_xml_files'] += 1
            document_id = normalize_text(root.get('id'))
            source = normalize_text(root.get('source'))
            url = normalize_text(root.get('url'))
            focus = element_text(root.find('Focus'))
            synonyms = _values(root, 'Synonym')
            umls_cuis = _values(root, 'CUI')
            semantic_types = _values(root, 'SemanticType')
            semantic_groups = _values(root, 'SemanticGroup')
            xml_path = path.relative_to(dataset_root).as_posix()

            for pair in pairs:
                stats['candidate_pairs'] += 1
                question_node = pair.find('Question')
                answer_node = pair.find('Answer')
                yield {
                    'document_id': document_id,
                    'question_id': normalize_text(
                        question_node.get('qid') if question_node is not None else ''
                    ),
                    'pair_id': normalize_text(pair.get('pid')),
                    'question_type': normalize_text(
                        question_node.get('qtype') if question_node is not None else ''
                    ),
                    'focus': focus,
                    'focus_synonyms': synonyms,
                    'question': element_text(question_node),
                    'answer': element_text(answer_node),
                    'source': source,
                    'url': url,
                    'collection': collection,
                    'xml_path': xml_path,
                    'umls_cuis': umls_cuis,
                    'semantic_types': semantic_types,
                    'semantic_groups': semantic_groups,
                }


def rejection_reason(
    record: dict[str, Any],
    min_question_chars: int,
    max_question_chars: int,
    min_answer_chars: int,
    max_answer_chars: int,
) -> str | None:
    required = (
        'document_id',
        'question_id',
        'question_type',
        'focus',
        'question',
        'answer',
        'source',
        'url',
        'collection',
        'xml_path',
    )
    for field in required:
        if not record[field]:
            return f'missing_{field}'
    question_size = len(record['question'])
    answer_size = len(record['answer'])
    if question_size < min_question_chars:
        return 'question_too_short'
    if question_size > max_question_chars:
        return 'question_too_long'
    if answer_size < min_answer_chars:
        return 'answer_too_short'
    if answer_size > max_answer_chars:
        return 'answer_too_long'
    return None


def curate(
    dataset_root: Path,
    output_path: Path,
    stats_path: Path,
    *,
    min_question_chars: int = DEFAULT_MIN_QUESTION_CHARS,
    max_question_chars: int = DEFAULT_MAX_QUESTION_CHARS,
    min_answer_chars: int = DEFAULT_MIN_ANSWER_CHARS,
    max_answer_chars: int = DEFAULT_MAX_ANSWER_CHARS,
) -> dict[str, Any]:
    '''Curate the dataset and atomically write JSONL plus statistics.'''
    if min_question_chars > max_question_chars:
        raise ValueError('Minimum question size exceeds maximum')
    if min_answer_chars > max_answer_chars:
        raise ValueError('Minimum answer size exceeds maximum')
    if not dataset_root.is_dir():
        raise FileNotFoundError(f'Dataset directory not found: {dataset_root}')

    stats: Counter[str] = Counter()
    seen_pairs: set[str] = set()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + '.tmp')
    output_hash = hashlib.sha256()

    try:
        with temporary_path.open('w', encoding='utf-8', newline='\n') as stream:
            for record in iter_candidates(dataset_root, stats):
                reason = rejection_reason(
                    record,
                    min_question_chars,
                    max_question_chars,
                    min_answer_chars,
                    max_answer_chars,
                )
                if reason:
                    stats[f'rejected_{reason}'] += 1
                    continue

                duplicate_key = hashlib.sha256(
                    (record['question'].casefold() + '\x00' + record['answer'].casefold())
                    .encode('utf-8')
                ).hexdigest()
                if duplicate_key in seen_pairs:
                    stats['rejected_exact_duplicate'] += 1
                    continue
                seen_pairs.add(duplicate_key)

                record = {'id': stable_id(record), **record}
                line = json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(',', ':'),
                    sort_keys=False,
                ) + '\n'
                stream.write(line)
                output_hash.update(line.encode('utf-8'))
                stats['output_records'] += 1
                stats['output_collection_' + record['collection']] += 1
                stats['output_question_type_' + record['question_type']] += 1
        os.replace(temporary_path, output_path)
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise

    ordered_stats: dict[str, Any] = {
        'dataset_root': portable_path(dataset_root),
        'output_path': output_path.as_posix(),
        'output_sha256': output_hash.hexdigest(),
        'rules': {
            'excluded_collections': sorted(COPYRIGHT_EXCLUDED),
            'min_question_chars': min_question_chars,
            'max_question_chars': max_question_chars,
            'min_answer_chars': min_answer_chars,
            'max_answer_chars': max_answer_chars,
            'duplicate_definition': 'normalized question + normalized answer, case-insensitive',
        },
        'counts': dict(sorted(stats.items())),
    }
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(
        json.dumps(ordered_stats, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    return ordered_stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--dataset',
        type=Path,
        default=Path('data/raw/MedQuAD-master'),
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/processed/medquad_curated.jsonl'),
    )
    parser.add_argument(
        '--stats',
        type=Path,
        default=Path('reports/evidence/medquad_curated_stats.json'),
    )
    parser.add_argument(
        '--min-question-chars', type=int, default=DEFAULT_MIN_QUESTION_CHARS
    )
    parser.add_argument(
        '--max-question-chars', type=int, default=DEFAULT_MAX_QUESTION_CHARS
    )
    parser.add_argument(
        '--min-answer-chars', type=int, default=DEFAULT_MIN_ANSWER_CHARS
    )
    parser.add_argument(
        '--max-answer-chars', type=int, default=DEFAULT_MAX_ANSWER_CHARS
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = curate(
        args.dataset,
        args.output,
        args.stats,
        min_question_chars=args.min_question_chars,
        max_question_chars=args.max_question_chars,
        min_answer_chars=args.min_answer_chars,
        max_answer_chars=args.max_answer_chars,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
