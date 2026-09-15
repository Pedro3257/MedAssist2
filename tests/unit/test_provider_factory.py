import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from medassist.infrastructure.config import ConfigurationError, load_env_file
from medassist.application.resilience import RetryingLLMProvider
from medassist.providers.factory import create_llm_provider, create_llm_runtime
from medassist.providers.google_ai import GoogleAIProvider
from medassist.providers.ollama import OllamaProvider


class ProviderFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env_file = Path(self.temp.name) / '.env'

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_env(self, content: str) -> None:
        self.env_file.write_text(content, encoding='utf-8')

    def test_loads_env_without_overwriting_existing_value(self) -> None:
        self.write_env("EXISTING=file-value\nQUOTED='quoted value'\n")

        with patch.dict(os.environ, {'EXISTING': 'system-value'}, clear=True):
            loaded = load_env_file(self.env_file)

            self.assertTrue(loaded)
            self.assertEqual(os.environ['EXISTING'], 'system-value')
            self.assertEqual(os.environ['QUOTED'], 'quoted value')

    def test_selects_ollama_and_its_model(self) -> None:
        self.write_env(
            'LLM_PROVIDER=ollama\n'
            'LLM_TIMEOUT_SECONDS=25\n'
            'LLM_MAX_RETRIES=3\n'
            'LLM_RETRY_DELAY_SECONDS=0.25\n'
            'LLM_RETRY_BACKOFF=1.5\n'
            'OLLAMA_BASE_URL=http://ollama.internal:11434/\n'
            'OLLAMA_MODEL=llama-test\n'
            'OLLAMA_LANGUAGE_REWRITE_MODEL=translator-test\n'
        )

        with patch.dict(os.environ, {}, clear=True):
            runtime = create_llm_runtime(self.env_file)

        self.assertIsInstance(runtime.provider, RetryingLLMProvider)
        self.assertIsInstance(runtime.provider.provider, OllamaProvider)
        self.assertEqual(
            runtime.provider.provider.base_url,
            'http://ollama.internal:11434',
        )
        self.assertEqual(runtime.provider.provider.timeout_seconds, 25)
        self.assertEqual(runtime.provider.policy.max_retries, 3)
        self.assertEqual(runtime.provider.policy.initial_delay_seconds, 0.25)
        self.assertEqual(runtime.provider.policy.backoff_multiplier, 1.5)
        self.assertEqual(runtime.model, 'llama-test')
        self.assertEqual(runtime.language_rewrite_model, 'translator-test')

    def test_selects_google_ai_and_its_model(self) -> None:
        self.write_env(
            'LLM_PROVIDER=google_ai\n'
            'LLM_TIMEOUT_SECONDS=30\n'
            'GEMINI_API_KEY=fake-test-key\n'
            'GOOGLE_AI_MODEL=gemini-test\n'
        )

        with patch.dict(os.environ, {}, clear=True):
            runtime = create_llm_runtime(self.env_file)

        self.assertIsInstance(runtime.provider, RetryingLLMProvider)
        self.assertIsInstance(runtime.provider.provider, GoogleAIProvider)
        self.assertEqual(runtime.provider.provider.timeout_seconds, 30)
        self.assertEqual(runtime.model, 'gemini-test')
        self.assertEqual(runtime.language_rewrite_model, 'gemini-test')

    def test_provider_helper_returns_only_selected_adapter(self) -> None:
        self.write_env('LLM_PROVIDER=ollama\n')

        with patch.dict(os.environ, {}, clear=True):
            provider = create_llm_provider(self.env_file)

        self.assertIsInstance(provider, RetryingLLMProvider)
        self.assertIsInstance(provider.provider, OllamaProvider)

    def test_rejects_unknown_provider(self) -> None:
        self.write_env('LLM_PROVIDER=unknown\n')

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigurationError):
                create_llm_runtime(self.env_file)

    def test_rejects_invalid_timeout(self) -> None:
        self.write_env('LLM_PROVIDER=ollama\nLLM_TIMEOUT_SECONDS=invalid\n')

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigurationError):
                create_llm_runtime(self.env_file)

    def test_rejects_invalid_env_line_without_exposing_value(self) -> None:
        self.write_env('INVALID LINE\n')

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ConfigurationError, 'Linha 1'):
                load_env_file(self.env_file)


if __name__ == '__main__':
    unittest.main()
