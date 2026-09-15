import json
import socket
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from medassist.application.llm import (
    LLMProvider,
    LLMProviderAuthenticationError,
    LLMProviderError,
    LLMProviderInvalidResponseError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
    LLMRequest,
    LLMResponse,
)

class OllamaProvider(LLMProvider):
    def __init__(
            self, 
            base_url: str = 'http://localhost:11434',
            timeout_seconds: float = 60.0,
        ) -> None:

        if not base_url.strip():
            raise ValueError('base_url não pode estar vazia')

        if timeout_seconds <= 0:
            raise ValueError('timeout_seconds deve ser maior que zero')

        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return 'ollama'

    def _build_payload(self, request: LLMRequest) -> dict:
        return {
            'model': request.model,
            'messages': [
                {
                    'role': 'system',
                    'content': request.system_prompt,
                },
                {
                    'role': 'user',
                    'content': request.user_prompt,
                },
            ],
            'stream': False,
            'options': {
                'temperature': request.temperature,
                'num_predict': request.max_tokens,
            },
        }

    def generate(self, request: LLMRequest) -> LLMResponse:
        payload = self._build_payload(request)
        body = json.dumps(payload).encode('utf-8')

        http_request = Request(
            url=f'{self.base_url}/api/chat',
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )

        started_at = perf_counter()

        try:
            with urlopen(
                http_request,
                timeout=self.timeout_seconds,
            ) as http_response:
                response_body = http_response.read().decode('utf-8')

        except HTTPError as error:
            self._raise_http_error(error)

        except (TimeoutError, socket.timeout) as error:
            raise LLMProviderTimeoutError(
                'O Ollama excedeu o tempo limite de resposta'
            ) from error

        except URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise LLMProviderTimeoutError(
                    'O Ollama excedeu o tempo limite de resposta'
                ) from error

            raise LLMProviderUnavailableError(
                'Não foi possível conectar ao Ollama'
            ) from error

        latency_ms = (perf_counter() - started_at) * 1000

        return self._parse_response(
            response_body=response_body,
            requested_model=request.model,
            latency_ms=latency_ms,
        )

    def _raise_http_error(self, error: HTTPError) -> None:
        if error.code in (401, 403):
            raise LLMProviderAuthenticationError(
                'O Ollama recusou a autenticação'
            ) from error

        if error.code in (408, 504):
            raise LLMProviderTimeoutError(
                'O Ollama excedeu o tempo limite de resposta'
            ) from error

        if error.code == 404:
            raise LLMProviderUnavailableError(
                'O endpoint ou modelo solicitado não foi encontrado no Ollama'
            ) from error

        if error.code == 429 or error.code >= 500:
            raise LLMProviderUnavailableError(
                f'O Ollama está indisponível: HTTP {error.code}'
            ) from error

        raise LLMProviderError(
            f'O Ollama recusou a requisição: HTTP {error.code}'
        ) from error

    def _parse_response(
        self,
        response_body: str,
        requested_model: str,
        latency_ms: float,
    ) -> LLMResponse:
        try:
            data = json.loads(response_body)
            message = data['message']
            content = message['content']
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise LLMProviderInvalidResponseError(
                'O Ollama retornou uma resposta inválida'
            ) from error

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderInvalidResponseError(
                'O Ollama retornou conteúdo vazio ou inválido'
            )

        model = data.get('model', requested_model)
        input_tokens = data.get('prompt_eval_count')
        output_tokens = data.get('eval_count')
        finish_reason = data.get('done_reason')

        if not isinstance(model, str) or not model.strip():
            raise LLMProviderInvalidResponseError(
                'O Ollama não informou um modelo válido'
            )

        if input_tokens is not None and not isinstance(input_tokens, int):
            raise LLMProviderInvalidResponseError(
                'O Ollama retornou input_tokens inválido'
            )

        if output_tokens is not None and not isinstance(output_tokens, int):
            raise LLMProviderInvalidResponseError(
                'O Ollama retornou output_tokens inválido'
            )

        if finish_reason is not None and not isinstance(finish_reason, str):
            raise LLMProviderInvalidResponseError(
                'O Ollama retornou finish_reason inválido'
            )

        return LLMResponse(
            content=content,
            provider=self.name,
            model=model,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            finish_reason=finish_reason,
        )
    