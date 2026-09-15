import json
import unittest
from io import BytesIO
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from medassist.application.llm import (
    LLMProviderAuthenticationError,
    LLMProviderError,
    LLMProviderInvalidResponseError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
    LLMRequest,
)
from medassist.providers.google_ai import GoogleAIProvider


class FakeHTTPResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> 'FakeHTTPResponse':
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def llm_request() -> LLMRequest:
    return LLMRequest(
        system_prompt='Assistente medico educacional.',
        user_prompt='O que e hipertensao?',
        model='gemini-test',
        temperature=0.2,
        max_tokens=128,
        correlation_id='test-google-001',
    )


class GoogleAIProviderTests(unittest.TestCase):
    def test_builds_request_and_maps_successful_response(self) -> None:
        response_data = {
            'candidates': [
                {
                    'content': {
                        'role': 'model',
                        'parts': [
                            {'text': 'Hipertensao e a elevacao persistente '},
                            {'text': 'da pressao arterial.'},
                        ],
                    },
                    'finishReason': 'STOP',
                },
            ],
            'usageMetadata': {
                'promptTokenCount': 24,
                'candidatesTokenCount': 17,
                'totalTokenCount': 41,
            },
            'modelVersion': 'gemini-test',
        }
        fake_response = FakeHTTPResponse(json.dumps(response_data).encode('utf-8'))
        provider = GoogleAIProvider(
            api_key='fake-secret-key',
            timeout_seconds=15,
        )

        with patch(
            'medassist.providers.google_ai.urlopen',
            return_value=fake_response,
        ) as mocked_urlopen:
            response = provider.generate(llm_request())

        http_request = mocked_urlopen.call_args.args[0]
        sent_payload = json.loads(http_request.data.decode('utf-8'))

        self.assertEqual(
            http_request.full_url,
            'https://generativelanguage.googleapis.com/v1beta/'
            'models/gemini-test:generateContent',
        )
        self.assertNotIn('fake-secret-key', http_request.full_url)
        self.assertEqual(
            http_request.get_header('X-goog-api-key'),
            'fake-secret-key',
        )
        self.assertEqual(http_request.method, 'POST')
        self.assertEqual(mocked_urlopen.call_args.kwargs['timeout'], 15)
        self.assertEqual(
            sent_payload['systemInstruction']['parts'][0]['text'],
            'Assistente medico educacional.',
        )
        self.assertEqual(sent_payload['contents'][0]['role'], 'user')
        self.assertEqual(sent_payload['generationConfig']['temperature'], 0.2)
        self.assertEqual(sent_payload['generationConfig']['maxOutputTokens'], 128)
        self.assertEqual(
            sent_payload['generationConfig']['thinkingConfig']['thinkingLevel'],
            'minimal',
        )
        self.assertEqual(
            response.content,
            'Hipertensao e a elevacao persistente da pressao arterial.',
        )
        self.assertEqual(response.provider, 'google_ai')
        self.assertEqual(response.model, 'gemini-test')
        self.assertEqual(response.input_tokens, 24)
        self.assertEqual(response.output_tokens, 17)
        self.assertEqual(response.finish_reason, 'STOP')
        self.assertGreaterEqual(response.latency_ms, 0)

    def test_reads_api_key_from_environment(self) -> None:
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'environment-key'}):
            provider = GoogleAIProvider()

        self.assertEqual(provider.name, 'google_ai')

    def test_rejects_missing_api_key_and_invalid_configuration(self) -> None:
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(LLMProviderAuthenticationError):
                GoogleAIProvider()

        with self.assertRaises(ValueError):
            GoogleAIProvider(api_key='fake-key', base_url='   ')

        with self.assertRaises(ValueError):
            GoogleAIProvider(api_key='fake-key', timeout_seconds=0)

    def test_rejects_invalid_or_empty_response(self) -> None:
        invalid_bodies = (
            b'not-json',
            json.dumps({'candidates': []}).encode('utf-8'),
            json.dumps({
                'candidates': [{'content': {'parts': [{'text': '   '}]}}],
            }).encode('utf-8'),
        )

        for body in invalid_bodies:
            with self.subTest(body=body):
                with patch(
                    'medassist.providers.google_ai.urlopen',
                    return_value=FakeHTTPResponse(body),
                ):
                    with self.assertRaises(LLMProviderInvalidResponseError):
                        GoogleAIProvider(api_key='fake-key').generate(llm_request())

    def test_maps_timeout_and_connection_error(self) -> None:
        cases = (
            (TimeoutError(), LLMProviderTimeoutError),
            (URLError('connection refused'), LLMProviderUnavailableError),
        )

        for error, expected_error in cases:
            with self.subTest(error=type(error).__name__):
                with patch(
                    'medassist.providers.google_ai.urlopen',
                    side_effect=error,
                ):
                    with self.assertRaises(expected_error):
                        GoogleAIProvider(api_key='fake-key').generate(llm_request())

    def test_maps_http_statuses_to_domain_errors(self) -> None:
        cases = (
            (401, LLMProviderAuthenticationError),
            (403, LLMProviderAuthenticationError),
            (408, LLMProviderTimeoutError),
            (404, LLMProviderUnavailableError),
            (429, LLMProviderUnavailableError),
            (500, LLMProviderUnavailableError),
            (400, LLMProviderError),
        )

        for status, expected_error in cases:
            error = HTTPError(
                url='https://generativelanguage.googleapis.com/test',
                code=status,
                msg='test error',
                hdrs=None,
                fp=BytesIO(b'{}'),
            )
            with self.subTest(status=status):
                with patch(
                    'medassist.providers.google_ai.urlopen',
                    side_effect=error,
                ):
                    with self.assertRaises(expected_error):
                        GoogleAIProvider(api_key='fake-key').generate(llm_request())


if __name__ == '__main__':
    unittest.main()
