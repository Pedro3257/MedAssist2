import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

from medassist.application.llm import LLMProviderAuthenticationError, LLMRequest
from medassist.providers.google_ai import GoogleAIProvider
from scripts.check_secrets import read_sensitive_values, scan_repository


class SecretSafetyTests(unittest.TestCase):
    def test_scanner_detects_secret_without_returning_its_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            secret = b'super-secret-value'
            (root / 'unsafe.txt').write_bytes(b'credential=' + secret)

            findings, scanned_files = scan_repository(
                root,
                {'GEMINI_API_KEY': secret},
            )

        self.assertEqual(scanned_files, 1)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, 'GEMINI_API_KEY')
        self.assertNotIn(secret.decode(), repr(findings[0]))

    def test_scanner_ignores_source_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            secret = 'super-secret-value'
            (root / '.env').write_text(
                f'GEMINI_API_KEY={secret}\n',
                encoding='utf-8',
            )
            values = read_sensitive_values(root / '.env')

            findings, scanned_files = scan_repository(root, values)

        self.assertEqual(scanned_files, 0)
        self.assertEqual(findings, [])

    def test_google_authentication_error_does_not_expose_key(self) -> None:
        secret = 'super-secret-value'
        provider = GoogleAIProvider(api_key=secret)
        request = LLMRequest(
            system_prompt='System prompt.',
            user_prompt='Question?',
            model='gemini-test',
        )
        error = HTTPError(
            url='https://generativelanguage.googleapis.com/test',
            code=401,
            msg='unauthorized',
            hdrs=None,
            fp=BytesIO(b'{}'),
        )

        with patch(
            'medassist.providers.google_ai.urlopen',
            side_effect=error,
        ):
            with self.assertRaises(LLMProviderAuthenticationError) as captured:
                provider.generate(request)

        self.assertNotIn(secret, str(captured.exception))
        self.assertNotIn(secret, repr(captured.exception))


if __name__ == '__main__':
    unittest.main()
