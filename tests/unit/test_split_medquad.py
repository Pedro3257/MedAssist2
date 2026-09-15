import json
import tempfile
import unittest
from pathlib import Path

from scripts.split_medquad import build_splits, focus_key


def record(index: int, focus: str) -> dict:
    return {
        'id': f'medquad_{index:04d}',
        'focus': focus,
        'collection': 'TestCollection',
        'question_type': 'information',
        'question': f'Question {index}?',
        'answer': f'Answer {index} with sufficient content.',
    }


class SplitMedquadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.input = self.root / 'curated.jsonl'
        self.output = self.root / 'splits'
        self.stats = self.root / 'stats.json'

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_records(self, records: list[dict]) -> None:
        with self.input.open('w', encoding='utf-8') as stream:
            for item in records:
                stream.write(json.dumps(item) + '\n')

    def load(self, name: str) -> list[dict]:
        return [
            json.loads(line)
            for line in (self.output / f'{name}.jsonl')
            .read_text(encoding='utf-8')
            .splitlines()
        ]

    def test_focus_normalization_is_case_and_space_insensitive(self) -> None:
        self.assertEqual(
            focus_key('  Example   DISEASE '),
            focus_key('example disease'),
        )

    def test_builds_disjoint_splits_and_evaluation_subset(self) -> None:
        records = []
        for group in range(1, 5):
            records.extend(
                (
                    record(group * 10, f'Disease {group}'),
                    record(group * 10 + 1, f'Disease {group}'),
                )
            )
        self.write_records(records)
        result = build_splits(
            self.input,
            self.output,
            self.stats,
            seed=7,
            target=8,
            minimum=5,
            maximum=10,
            evaluation_size=2,
        )

        splits = {name: self.load(name) for name in ('train', 'validation', 'test')}
        focus_sets = {
            name: {focus_key(item['focus']) for item in items}
            for name, items in splits.items()
        }
        self.assertFalse(focus_sets['train'] & focus_sets['validation'])
        self.assertFalse(focus_sets['train'] & focus_sets['test'])
        self.assertFalse(focus_sets['validation'] & focus_sets['test'])
        self.assertEqual(sum(len(items) for items in splits.values()), 8)
        test_ids = {item['id'] for item in splits['test']}
        evaluation_ids = {item['id'] for item in self.load('evaluation')}
        self.assertTrue(evaluation_ids <= test_ids)
        self.assertEqual(result['selection']['selected_records'], 8)

    def test_generation_is_deterministic(self) -> None:
        self.write_records(
            [record(index, f'Disease {index // 2}') for index in range(20)]
        )
        first = build_splits(
            self.input,
            self.output,
            self.stats,
            seed=42,
            target=10,
            minimum=5,
            maximum=15,
            evaluation_size=2,
        )
        contents = {
            name: (self.output / f'{name}.jsonl').read_bytes()
            for name in ('train', 'validation', 'test', 'evaluation')
        }
        second = build_splits(
            self.input,
            self.output,
            self.stats,
            seed=42,
            target=10,
            minimum=5,
            maximum=15,
            evaluation_size=2,
        )
        for name, content in contents.items():
            self.assertEqual(content, (self.output / f'{name}.jsonl').read_bytes())
        self.assertEqual(first['splits'], second['splits'])

    def test_rejects_target_outside_mvp_range(self) -> None:
        self.write_records([record(1, 'Disease')])
        with self.assertRaises(ValueError):
            build_splits(
                self.input,
                self.output,
                self.stats,
                target=2,
                minimum=3,
                maximum=8,
            )


if __name__ == '__main__':
    unittest.main()
