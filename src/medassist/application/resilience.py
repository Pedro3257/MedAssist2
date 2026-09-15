from collections.abc import Callable
from dataclasses import dataclass, replace
from time import perf_counter, sleep

from medassist.application.llm import (
    LLMProvider,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
    LLMRequest,
    LLMResponse,
)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_retries: int = 2
    initial_delay_seconds: float = 0.5
    backoff_multiplier: float = 2.0

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError('max_retries nao pode ser negativo')
        if self.initial_delay_seconds < 0:
            raise ValueError('initial_delay_seconds nao pode ser negativo')
        if self.backoff_multiplier < 1:
            raise ValueError('backoff_multiplier deve ser pelo menos 1')


class RetryingLLMProvider(LLMProvider):
    def __init__(
        self,
        provider: LLMProvider,
        policy: RetryPolicy | None = None,
        sleeper: Callable[[float], None] = sleep,
    ) -> None:
        self.provider = provider
        self.policy = policy or RetryPolicy()
        self._sleeper = sleeper

    @property
    def name(self) -> str:
        return self.provider.name

    def generate(self, request: LLMRequest) -> LLMResponse:
        started_at = perf_counter()
        delay_seconds = self.policy.initial_delay_seconds

        for retry_number in range(self.policy.max_retries + 1):
            try:
                response = self.provider.generate(request)
                total_latency_ms = (perf_counter() - started_at) * 1000
                return replace(response, latency_ms=total_latency_ms)
            except (
                LLMProviderTimeoutError,
                LLMProviderUnavailableError,
            ):
                if retry_number >= self.policy.max_retries:
                    raise
                self._sleeper(delay_seconds)
                delay_seconds *= self.policy.backoff_multiplier

        raise AssertionError('Fluxo de retry terminou em estado impossivel')
