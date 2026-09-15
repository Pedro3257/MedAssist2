import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_medquad import curate, normalize_text


def write_document(
    root: Path,
    collection: str,
    filename: str,
    pairs: str,
    *,
    document_id: str = 'doc-1',
    source: str = 'UnitTest',
    focus: str = 'Example Disease',
) -> None:
    folder = root / collection
    folder.mkdir(parents=True, exist_ok=True)
    xml = f'''<?xml version='1.0' encoding='UTF-8'?>
<Document id='{document_id}' source='{source}' url='https://example.org/source'>
  <Focus>{focus}</Focus>
  <FocusAnnotations>
    <UMLS>
      <CUIs><CUI>C0000001</CUI></CUIs>
      <SemanticTypes><SemanticType>T047</SemanticType></SemanticTypes>
      <SemanticGroup>Disorders</SemanticGroup>
    </UMLS>
  </FocusAnnotations>
  <QAPairs>{pairs}</QAPairs>
</Document>'''
    (folder / filename).write_text(xml, encoding='utf-8')


def qa(pid: str, question: str, answer: str, qtype: str = 'information') -> str:
    return f'''<QAPair pid='{pid}'>
<Question qid='q-{pid}' qtype='{qtype}'>{question}</Question>
<Answer>{answer}</Answer>
</QAPair>'''


class NormalizeTextTests(unittest.TestCase):
    def test_normalizes_unicode_whitespace_entities_and_html(self) -> None:
        value = '  Café\u0301  &amp;  &lt;b&gt;medical&lt;/b&gt;\n text  '
        self.assertEqual(normalize_text(value), 'Café́ & medical text')


class CurateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dataset = self.root / 'raw'
        self.output = self.root / 'processed' / 'curated.jsonl'
        self.stats = self.root / 'reports' / 'stats.json'

    def tearDown(self) -> None:
        self.temp.cleanup()

    def records(self) -> list[dict]:
        return [
            json.loads(line)
            for line in self.output.read_text(encoding='utf-8').splitlines()
        ]

    def test_curates_normalizes_preserves_metadata_and_deduplicates(self) -> None:
        answer = 'A sufficiently detailed answer with useful medical context.'
        pairs = ''.join(
            (
                qa('1', 'What   is Example Disease?', answer),
                qa('2', 'What   is Example Disease?', answer),
                qa('3', 'What are the symptoms?', 'short'),
            )
        )
        write_document(self.dataset, '1_Valid_QA', 'one.xml', pairs)

        result = curate(self.dataset, self.output, self.stats)
        records = self.records()

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['question'], 'What is Example Disease?')
        self.assertEqual(record['collection'], '1_Valid_QA')
        self.assertEqual(record['source'], 'UnitTest')
        self.assertEqual(record['url'], 'https://example.org/source')
        self.assertEqual(record['umls_cuis'], ['C0000001'])
        self.assertTrue(record['id'].startswith('medquad_'))
        self.assertEqual(result['counts']['rejected_exact_duplicate'], 1)
        self.assertEqual(result['counts']['rejected_answer_too_short'], 1)

    def test_excludes_copyright_collection_and_empty_answer(self) -> None:
        write_document(
            self.dataset,
            '10_MPlus_ADAM_QA',
            'excluded.xml',
            qa('1', 'A valid question?', 'A long answer that must not be exported.'),
        )
        write_document(
            self.dataset,
            '2_GARD_QA',
            'empty.xml',
            qa('2', 'Another valid question?', ''),
        )

        result = curate(self.dataset, self.output, self.stats)

        self.assertEqual(self.records(), [])
        self.assertEqual(result['counts']['copyright_excluded_pairs'], 1)
        self.assertEqual(result['counts']['rejected_missing_answer'], 1)

    def test_rejects_missing_source_to_guarantee_traceability(self) -> None:
        write_document(
            self.dataset,
            '6_NINDS_QA',
            'missing.xml',
            qa('1', 'What is this disease?', 'A complete and valid medical answer.'),
            source='',
        )
        result = curate(self.dataset, self.output, self.stats)
        self.assertEqual(result['counts']['rejected_missing_source'], 1)
        self.assertEqual(self.records(), [])

    def test_output_is_deterministic(self) -> None:
        write_document(
            self.dataset,
            '1_Valid_QA',
            'one.xml',
            qa('1', 'What is this disease?', 'A complete and valid medical answer.'),
        )
        first = curate(self.dataset, self.output, self.stats)
        first_content = self.output.read_bytes()
        second = curate(self.dataset, self.output, self.stats)
        self.assertEqual(first_content, self.output.read_bytes())
        self.assertEqual(first['output_sha256'], second['output_sha256'])

    def test_invalid_limits_fail_fast(self) -> None:
        self.dataset.mkdir()
        with self.assertRaises(ValueError):
            curate(
                self.dataset,
                self.output,
                self.stats,
                min_question_chars=100,
                max_question_chars=10,
            )


if __name__ == '__main__':
    unittest.main()
