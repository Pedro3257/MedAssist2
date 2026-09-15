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
from medassist.providers.ollama import OllamaProvider


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
        model='llama-test',
        temperature=0.2,
        max_tokens=128,
        correlation_id='test-ollama-001',
    )


class OllamaProviderTests(unittest.TestCase):
    def test_builds_request_and_maps_successful_response(self) -> None:
        response_data = {
            'model': 'llama-test',
            'message': {
                'role': 'assistant',
                'content': 'Hipertensao e a elevacao persistente da pressao arterial.',
            },
            'done': True,
            'done_reason': 'stop',
            'prompt_eval_count': 24,
            'eval_count': 17,
        }
        fake_response = FakeHTTPResponse(json.dumps(response_data).encode('utf-8'))
        provider = OllamaProvider(
            base_url='http://localhost:11434/',
            timeout_seconds=15,
        )

        with patch(
            'medassist.providers.ollama.urlopen',
            return_value=fake_response,
        ) as mocked_urlopen:
            response = provider.generate(llm_request())

        http_request = mocked_urlopen.call_args.args[0]
        sent_payload = json.loads(http_request.data.decode('utf-8'))

        self.assertEqual(http_request.full_url, 'http://localhost:11434/api/chat')
        self.assertEqual(http_request.method, 'POST')
        self.assertEqual(mocked_urlopen.call_args.kwargs['timeout'], 15)
        self.assertEqual(sent_payload['model'], 'llama-test')
        self.assertFalse(sent_payload['stream'])
        self.assertEqual(sent_payload['messages'][0]['role'], 'system')
        self.assertEqual(sent_payload['messages'][1]['role'], 'user')
        self.assertEqual(sent_payload['options']['temperature'], 0.2)
        self.assertEqual(sent_payload['options']['num_predict'], 128)
        self.assertEqual(response.content, response_data['message']['content'])
        self.assertEqual(response.provider, 'ollama')
        self.assertEqual(response.model, 'llama-test')
        self.assertEqual(response.input_tokens, 24)
        self.assertEqual(response.output_tokens, 17)
        self.assertEqual(response.finish_reason, 'stop')
        self.assertGreaterEqual(response.latency_ms, 0)

    def test_rejects_invalid_configuration(self) -> None:
        with self.assertRaises(ValueError):
            OllamaProvider(base_url='   ')

        with self.assertRaises(ValueError):
            OllamaProvider(timeout_seconds=0)

    def test_rejects_invalid_json_response(self) -> None:
        fake_response = FakeHTTPResponse(b'not-json')

        with patch(
            'medassist.providers.ollama.urlopen',
            return_value=fake_response,
        ):
            with self.assertRaises(LLMProviderInvalidResponseError):
                OllamaProvider().generate(llm_request())

    def test_rejects_empty_content(self) -> None:
        body = json.dumps({'message': {'content': '   '}}).encode('utf-8')

        with patch(
            'medassist.providers.ollama.urlopen',
            return_value=FakeHTTPResponse(body),
        ):
            with self.assertRaises(LLMProviderInvalidResponseError):
                OllamaProvider().generate(llm_request())

    def test_maps_socket_timeout(self) -> None:
        with patch(
            'medassist.providers.ollama.urlopen',
            side_effect=TimeoutError(),
        ):
            with self.assertRaises(LLMProviderTimeoutError):
                OllamaProvider().generate(llm_request())

    def test_maps_connection_error_to_unavailable(self) -> None:
        with patch(
            'medassist.providers.ollama.urlopen',
            side_effect=URLError('connection refused'),
        ):
            with self.assertRaises(LLMProviderUnavailableError):
                OllamaProvider().generate(llm_request())

    def test_maps_http_statuses_to_domain_errors(self) -> None:
        cases = (
            (401, LLMProviderAuthenticationError),
            (408, LLMProviderTimeoutError),
            (404, LLMProviderUnavailableError),
            (429, LLMProviderUnavailableError),
            (500, LLMProviderUnavailableError),
            (400, LLMProviderError),
        )

        for status, expected_error in cases:
            error = HTTPError(
                url='http://localhost:11434/api/chat',
                code=status,
                msg='test error',
                hdrs=None,
                fp=BytesIO(b'{}'),
            )
            with self.subTest(status=status):
                with patch(
                    'medassist.providers.ollama.urlopen',
                    side_effect=error,
                ):
                    with self.assertRaises(expected_error):
                        OllamaProvider().generate(llm_request())


if __name__ == '__main__':
    unittest.main()
