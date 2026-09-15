from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class LLMRequest:
    system_prompt: str
    user_prompt: str
    model: str
    temperature: float = 0.1
    max_tokens: int = 512
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.system_prompt.strip():
            raise ValueError("system_prompt não pode estar vazio")
        
        if not self.user_prompt.strip():
            raise ValueError("user_prompt não pode estar vazio")
        
        if not self.model.strip():
            raise ValueError("model não pode estar vazio")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature deve estar entre 0.0 e 2.0")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens deve ser maior que zero")
        
        if self.correlation_id is not None and not self.correlation_id.strip():
            raise ValueError("correlation_id não pode ser vazio")

@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str
    provider: str
    model: str
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    finish_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError('content não pode estar vazio')

        if not self.provider.strip():
            raise ValueError('provider não pode estar vazio')

        if not self.model.strip():
            raise ValueError('model não pode estar vazio')

        if self.latency_ms < 0:
            raise ValueError('latency_ms não pode ser negativa')

        if self.input_tokens is not None and self.input_tokens < 0:
            raise ValueError('input_tokens não pode ser negativo')

        if self.output_tokens is not None and self.output_tokens < 0:
            raise ValueError('output_tokens não pode ser negativo')
        
class LLMProviderError(Exception):
    """Erro base relacionado à execução de um provider de LLM."""

class LLMProviderTimeoutError(LLMProviderError):
    """O provider não respondeu dentro do tempo limite."""

class LLMProviderUnavailableError(LLMProviderError):
    """O provider está temporariamente indisponível."""

class LLMProviderAuthenticationError(LLMProviderError):
    """As credenciais fornecidas ao provider são inválidas."""

class LLMProviderInvalidResponseError(LLMProviderError):
    """O provider retornou uma resposta ausente ou inválida."""

class LLMProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Retorna o identificador público do provider."""

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Gera uma resposta usando o provider configurado."""
