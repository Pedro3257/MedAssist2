#!/usr/bin/env python3
'''Select the MedQuAD MVP and split it by medical focus without leakage.'''

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_SEED = 42
DEFAULT_TARGET = 6000
DEFAULT_EVALUATION_SIZE = 50
SPLIT_RATIOS = {'train': 0.8, 'validation': 0.1, 'test': 0.1}


def focus_key(value: str) -> str:
    value = unicodedata.normalize('NFC', value).casefold()
    return re.sub(r'\s+', ' ', value).strip()


def rank(seed: int, namespace: str, value: str) -> str:
    payload = str(seed) + '|' + namespace + '|' + value
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open('r', encoding='utf-8') as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not record.get('id') or not record.get('focus'):
                raise ValueError(f'Invalid record at line {line_number}')
            records.append(record)
    return records


def select_groups(
    groups: dict[str, list[dict[str, Any]]],
    seed: int,
    target: int,
    minimum: int,
    maximum: int,
) -> list[str]:
    if not minimum <= target <= maximum:
        raise ValueError('Target must be inside the configured MVP range')
    ordered = sorted(groups, key=lambda key: rank(seed, 'selection', key))
    selected: list[str] = []
    count = 0
    for key in ordered:
        size = len(groups[key])
        if count + size <= target:
            selected.append(key)
            count += size
        if count == target:
            break
    if count < minimum:
        raise ValueError(f'Only {count} records could be selected')
    return selected


def assign_splits(
    groups: dict[str, list[dict[str, Any]]],
    selected: list[str],
    seed: int,
) -> dict[str, list[dict[str, Any]]]:
    total = sum(len(groups[key]) for key in selected)
    targets = {name: total * ratio for name, ratio in SPLIT_RATIOS.items()}
    outputs: dict[str, list[dict[str, Any]]] = {
        name: [] for name in SPLIT_RATIOS
    }
    ordered = sorted(selected, key=lambda key: rank(seed, 'split', key))
    for key in ordered:
        destination = min(
            outputs,
            key=lambda name: (
                len(outputs[name]) / targets[name],
                name,
            ),
        )
        outputs[destination].extend(groups[key])
    for records in outputs.values():
        records.sort(key=lambda record: record['id'])
    return outputs


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    digest = hashlib.sha256()
    try:
        with temporary.open('w', encoding='utf-8', newline='\n') as stream:
            for record in records:
                line = json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(',', ':'),
                ) + '\n'
                stream.write(line)
                digest.update(line.encode('utf-8'))
        os.replace(temporary, path)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    return digest.hexdigest()


def build_splits(
    input_path: Path,
    output_dir: Path,
    stats_path: Path,
    *,
    seed: int = DEFAULT_SEED,
    target: int = DEFAULT_TARGET,
    minimum: int = 3000,
    maximum: int = 8000,
    evaluation_size: int = DEFAULT_EVALUATION_SIZE,
) -> dict[str, Any]:
    records = read_jsonl(input_path)
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[focus_key(record['focus'])].append(record)

    selected = select_groups(groups, seed, target, minimum, maximum)
    splits = assign_splits(groups, selected, seed)
    evaluation = sorted(
        splits['test'],
        key=lambda record: rank(seed, 'evaluation', record['id']),
    )[:evaluation_size]

    hashes = {}
    for name, output_records in (*splits.items(), ('evaluation', evaluation)):
        hashes[name] = write_jsonl(output_dir / f'{name}.jsonl', output_records)

    focus_sets = {
        name: {focus_key(record['focus']) for record in output_records}
        for name, output_records in splits.items()
    }
    id_sets = {
        name: {record['id'] for record in output_records}
        for name, output_records in splits.items()
    }
    overlaps = {}
    names = list(splits)
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            overlaps[left + '_vs_' + right] = {
                'focuses': len(focus_sets[left] & focus_sets[right]),
                'records': len(id_sets[left] & id_sets[right]),
            }

    selected_records = [record for name in splits for record in splits[name]]
    collection_counts = Counter(record['collection'] for record in selected_records)
    qtype_counts = Counter(record['question_type'] for record in selected_records)
    result: dict[str, Any] = {
        'input_path': input_path.as_posix(),
        'output_dir': output_dir.as_posix(),
        'seed': seed,
        'selection': {
            'available_records': len(records),
            'available_focuses': len(groups),
            'target_records': target,
            'selected_records': len(selected_records),
            'selected_focuses': len(selected),
            'minimum_records': minimum,
            'maximum_records': maximum,
        },
        'splits': {
            name: {
                'records': len(output_records),
                'focuses': len(focus_sets[name]),
                'sha256': hashes[name],
            }
            for name, output_records in splits.items()
        },
        'evaluation': {
            'records': len(evaluation),
            'focuses': len({focus_key(record['focus']) for record in evaluation}),
            'source': 'deterministic subset of test',
            'sha256': hashes['evaluation'],
        },
        'overlaps': overlaps,
        'selected_by_collection': dict(sorted(collection_counts.items())),
        'selected_by_question_type': dict(sorted(qtype_counts.items())),
    }
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/processed/medquad_curated.jsonl'),
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/processed'),
    )
    parser.add_argument(
        '--stats',
        type=Path,
        default=Path('reports/evidence/dataset_split_stats.json'),
    )
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED)
    parser.add_argument('--target', type=int, default=DEFAULT_TARGET)
    parser.add_argument(
        '--evaluation-size',
        type=int,
        default=DEFAULT_EVALUATION_SIZE,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_splits(
        args.input,
        args.output_dir,
        args.stats,
        seed=args.seed,
        target=args.target,
        evaluation_size=args.evaluation_size,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
