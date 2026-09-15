import unittest

from medassist.application.llm import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
)


class FakeLLMProvider(LLMProvider):
    def __init__(self, content: str = 'Resposta simulada.') -> None:
        self.content = content
        self.last_request: LLMRequest | None = None

    @property
    def name(self) -> str:
        return 'fake'

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.last_request = request
        return LLMResponse(
            content=self.content,
            provider=self.name,
            model=request.model,
            latency_ms=1.0,
            input_tokens=10,
            output_tokens=5,
            finish_reason='stop',
        )


class LLMProviderTests(unittest.TestCase):
    def test_fake_provider_generates_standard_response(self) -> None:
        provider = FakeLLMProvider()
        request = LLMRequest(
            system_prompt='Assistente medico educacional.',
            user_prompt='O que e hipertensao?',
            model='fake-model',
            temperature=0.5,
            max_tokens=50,
            correlation_id='test-001',
        )

        response = provider.generate(request)

        self.assertEqual(provider.name, 'fake')
        self.assertEqual(response.content, 'Resposta simulada.')
        self.assertEqual(response.provider, 'fake')
        self.assertEqual(response.model, 'fake-model')
        self.assertEqual(response.finish_reason, 'stop')
        self.assertIs(provider.last_request, request)

    def test_request_rejects_empty_user_prompt(self) -> None:
        with self.assertRaises(ValueError):
            LLMRequest(
                system_prompt='Assistente medico educacional.',
                user_prompt='   ',
                model='fake-model',
            )


if __name__ == '__main__':
    unittest.main()
