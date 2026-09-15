import unittest

from medassist.application.prompts import (
    MEDASSIST_SYSTEM_PROMPT,
    SYSTEM_PROMPT_VERSION,
    get_system_prompt,
)


class SystemPromptTests(unittest.TestCase):
    def test_prompt_is_versioned_and_not_empty(self) -> None:
        self.assertRegex(SYSTEM_PROMPT_VERSION, r'^\d+\.\d+\.\d+$')
        self.assertTrue(MEDASSIST_SYSTEM_PROMPT.strip())
        self.assertEqual(get_system_prompt(), MEDASSIST_SYSTEM_PROMPT)

    def test_prompt_contains_mandatory_safety_rules(self) -> None:
        normalized = MEDASSIST_SYSTEM_PROMPT.casefold()
        required_terms = (
            'evidências',
            'abstenha-se',
            'prescrição',
            'dosagem individualizada',
            'diagnóstico definitivo',
            'urgência',
            'fontes',
            'dados sintéticos',
            'validação humana',
        )

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term.casefold(), normalized)

    def test_prompt_does_not_contain_secret_placeholders(self) -> None:
        normalized = MEDASSIST_SYSTEM_PROMPT.casefold()
        forbidden_terms = (
            'gemini_api_key',
            'x-goog-api-key',
            'postgres_password',
            'replace-with-your',
        )

        for term in forbidden_terms:
            with self.subTest(term=term):
                self.assertNotIn(term, normalized)


if __name__ == '__main__':
    unittest.main()
