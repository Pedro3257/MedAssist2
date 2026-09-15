import os
import unittest

from medassist.application.llm import LLMRequest
from medassist.application.prompts import get_system_prompt
from medassist.providers.ollama import OllamaProvider


RUN_OLLAMA_INTEGRATION = os.getenv('RUN_OLLAMA_INTEGRATION') == '1'


@unittest.skipUnless(
    RUN_OLLAMA_INTEGRATION,
    'Defina RUN_OLLAMA_INTEGRATION=1 para testar o Ollama local.',
)
class OllamaProviderIntegrationTests(unittest.TestCase):
    def test_generates_response_with_local_model(self) -> None:
        model = os.getenv('OLLAMA_MODEL', 'llama3.2:1b')
        provider = OllamaProvider(timeout_seconds=120)
        request = LLMRequest(
            system_prompt=get_system_prompt(),
            user_prompt='Em uma frase, o que e hipertensao arterial?',
            model=model,
            temperature=0.1,
            max_tokens=64,
            correlation_id='ollama-integration-001',
        )

        response = provider.generate(request)

        self.assertEqual(response.provider, 'ollama')
        self.assertEqual(response.model, model)
        self.assertTrue(response.content.strip())
        self.assertGreaterEqual(response.latency_ms, 0)
        self.assertIsInstance(response.input_tokens, int)
        self.assertIsInstance(response.output_tokens, int)
        self.assertGreater(response.output_tokens, 0)


if __name__ == '__main__':
    unittest.main()
