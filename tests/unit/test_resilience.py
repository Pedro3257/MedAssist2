import unittest

from medassist.application.llm import (
    LLMProvider,
    LLMProviderAuthenticationError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
    LLMRequest,
    LLMResponse,
)
from medassist.application.resilience import RetryPolicy, RetryingLLMProvider


def request() -> LLMRequest:
    return LLMRequest(
        system_prompt='System prompt.',
        user_prompt='Test question?',
        model='test-model',
    )


def response() -> LLMResponse:
    return LLMResponse(
        content='Test response.',
        provider='fake',
        model='test-model',
        latency_ms=1,
    )


class SequencedProvider(LLMProvider):
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.calls = 0

    @property
    def name(self) -> str:
        return 'fake'

    def generate(self, llm_request: LLMRequest) -> LLMResponse:
        outcome = self.outcomes[self.calls]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        if not isinstance(outcome, LLMResponse):
            raise AssertionError('Resultado de teste invalido')
        return outcome


class RetryingLLMProviderTests(unittest.TestCase):
    def test_retries_transient_errors_and_then_succeeds(self) -> None:
        provider = SequencedProvider([
            LLMProviderUnavailableError('unavailable'),
            LLMProviderTimeoutError('timeout'),
            response(),
        ])
        delays: list[float] = []
        retrying = RetryingLLMProvider(
            provider,
            RetryPolicy(
                max_retries=2,
                initial_delay_seconds=0.1,
                backoff_multiplier=2,
            ),
            sleeper=delays.append,
        )

        result = retrying.generate(request())

        self.assertEqual(provider.calls, 3)
        self.assertEqual(delays, [0.1, 0.2])
        self.assertEqual(result.content, 'Test response.')
        self.assertEqual(result.provider, 'fake')
        self.assertGreaterEqual(result.latency_ms, 0)

    def test_reraises_last_error_when_retries_are_exhausted(self) -> None:
        provider = SequencedProvider([
            LLMProviderUnavailableError('first'),
            LLMProviderUnavailableError('last'),
        ])
        retrying = RetryingLLMProvider(
            provider,
            RetryPolicy(max_retries=1, initial_delay_seconds=0),
            sleeper=lambda _: None,
        )

        with self.assertRaisesRegex(LLMProviderUnavailableError, 'last'):
            retrying.generate(request())

        self.assertEqual(provider.calls, 2)

    def test_does_not_retry_non_transient_error(self) -> None:
        provider = SequencedProvider([
            LLMProviderAuthenticationError('invalid credentials'),
        ])
        retrying = RetryingLLMProvider(
            provider,
            RetryPolicy(max_retries=3, initial_delay_seconds=0),
            sleeper=lambda _: self.fail('sleep nao deveria ser chamado'),
        )

        with self.assertRaises(LLMProviderAuthenticationError):
            retrying.generate(request())

        self.assertEqual(provider.calls, 1)

    def test_rejects_invalid_retry_policy(self) -> None:
        invalid_arguments = (
            {'max_retries': -1},
            {'initial_delay_seconds': -0.1},
            {'backoff_multiplier': 0.5},
        )

        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    RetryPolicy(**arguments)


if __name__ == '__main__':
    unittest.main()
