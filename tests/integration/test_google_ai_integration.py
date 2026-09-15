import os
import unittest
from pathlib import Path

from dotenv import load_dotenv

from medassist.application.llm import LLMRequest
from medassist.application.prompts import get_system_prompt
from medassist.providers.google_ai import GoogleAIProvider


# Carrega as credenciais locais antes de avaliar a flag de integração.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / '.env')

RUN_GOOGLE_AI_INTEGRATION = os.getenv('RUN_GOOGLE_AI_INTEGRATION') == '1'


@unittest.skipUnless(
    RUN_GOOGLE_AI_INTEGRATION,
    'Defina RUN_GOOGLE_AI_INTEGRATION=1 para testar o Google AI.',
)
class GoogleAIProviderIntegrationTests(unittest.TestCase):
    def test_generates_response_with_remote_model(self) -> None:
        model = os.getenv('GOOGLE_AI_MODEL', 'gemini-3.6-flash')
        provider = GoogleAIProvider(timeout_seconds=60)
        request = LLMRequest(
            system_prompt=get_system_prompt(),
            user_prompt='Em uma frase, o que e hipertensao arterial?',
            model=model,
            temperature=0.1,
            max_tokens=64,
            correlation_id='google-ai-integration-001',
        )

        response = provider.generate(request)

        self.assertEqual(response.provider, 'google_ai')
        self.assertTrue(response.model.strip())
        self.assertTrue(response.content.strip())
        self.assertGreaterEqual(response.latency_ms, 0)
        self.assertIsInstance(response.input_tokens, int)
        self.assertIsInstance(response.output_tokens, int)
        self.assertGreater(response.output_tokens, 0)


if __name__ == '__main__':
    unittest.main()
