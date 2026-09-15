import json
import tempfile
import unittest
from pathlib import Path

from medassist.application.llm import (
    LLMProvider,
    LLMProviderUnavailableError,
    LLMRequest,
    LLMResponse,
)
from medassist.providers.factory import LLMRuntime
from scripts.run_llm_baseline import load_records, run_baseline


class FakeBaselineProvider(LLMProvider):
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    @property
    def name(self) -> str:
        return 'fake'

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        if self.fail:
            raise LLMProviderUnavailableError('provider unavailable')
        return LLMResponse(
            content=f'Response to: {request.user_prompt}',
            provider=self.name,
            model=request.model,
            latency_ms=12.5,
            input_tokens=10,
            output_tokens=8,
            finish_reason='stop',
        )


def evaluation_record(identifier: str = 'record-1') -> dict:
    return {
        'id': identifier,
        'question': 'What is hypertension?',
        'answer': 'Reference answer.',
        'focus': 'Hypertension',
        'question_type': 'information',
        'source': 'Test Source',
        'url': 'https://example.test/source',
    }


class LLMBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.output = self.root / 'baseline.jsonl'

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_records_response_metadata_and_no_secret(self) -> None:
        provider = FakeBaselineProvider()
        runtime = LLMRuntime(provider=provider, model='base-model')

        stats = run_baseline(
            [evaluation_record()],
            runtime,
            self.output,
        )
        item = json.loads(self.output.read_text(encoding='utf-8'))

        self.assertEqual(stats['success'], 1)
        self.assertEqual(item['status'], 'success')
        self.assertEqual(item['provider'], 'fake')
        self.assertEqual(item['model'], 'base-model')
        self.assertEqual(item['latency_ms'], 12.5)
        self.assertEqual(item['input_tokens'], 10)
        self.assertEqual(item['output_tokens'], 8)
        self.assertEqual(item['reference_answer'], 'Reference answer.')
        self.assertNotIn('api_key', self.output.read_text(encoding='utf-8').lower())

    def test_records_controlled_provider_error(self) -> None:
        runtime = LLMRuntime(
            provider=FakeBaselineProvider(fail=True),
            model='base-model',
        )

        stats = run_baseline(
            [evaluation_record()],
            runtime,
            self.output,
        )
        item = json.loads(self.output.read_text(encoding='utf-8'))

        self.assertEqual(stats['error'], 1)
        self.assertEqual(item['status'], 'error')
        self.assertEqual(item['error_type'], 'LLMProviderUnavailableError')
        self.assertNotIn('response', item)

    def test_resume_skips_existing_identifier(self) -> None:
        provider = FakeBaselineProvider()
        runtime = LLMRuntime(provider=provider, model='base-model')
        records = [evaluation_record('one'), evaluation_record('two')]
        run_baseline(records[:1], runtime, self.output)

        stats = run_baseline(records, runtime, self.output, resume=True)

        lines = self.output.read_text(encoding='utf-8').splitlines()
        self.assertEqual(stats['skipped'], 1)
        self.assertEqual(stats['success'], 1)
        self.assertEqual(len(lines), 2)
        self.assertEqual(provider.calls, 2)

    def test_load_records_validates_and_limits_input(self) -> None:
        input_path = self.root / 'evaluation.jsonl'
        records = [evaluation_record('one'), evaluation_record('two')]
        input_path.write_text(
            ''.join(json.dumps(item) + '\n' for item in records),
            encoding='utf-8',
        )

        loaded = load_records(input_path, limit=1)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]['id'], 'one')


if __name__ == '__main__':
    unittest.main()
