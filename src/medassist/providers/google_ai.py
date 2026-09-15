import json
import os
import socket
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import quote
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


class GoogleAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = 'https://generativelanguage.googleapis.com/v1beta',
        timeout_seconds: float = 60.0,
    ) -> None:
        resolved_api_key = api_key or os.getenv('GEMINI_API_KEY')

        if not resolved_api_key or not resolved_api_key.strip():
            raise LLMProviderAuthenticationError(
                'GEMINI_API_KEY nao foi configurada'
            )

        if not base_url.strip():
            raise ValueError('base_url nao pode estar vazia')

        if timeout_seconds <= 0:
            raise ValueError('timeout_seconds deve ser maior que zero')

        self._api_key = resolved_api_key.strip()
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return 'google_ai'

    def _build_payload(self, request: LLMRequest) -> dict:
        return {
            'systemInstruction': {
                'parts': [{'text': request.system_prompt}],
            },
            'contents': [
                {
                    'role': 'user',
                    'parts': [{'text': request.user_prompt}],
                },
            ],
            'generationConfig': {
                'temperature': request.temperature,
                'maxOutputTokens': request.max_tokens,
                'thinkingConfig': {
                    'thinkingLevel': 'minimal',
                },
            },
        }

    def generate(self, request: LLMRequest) -> LLMResponse:
        model_path = quote(request.model, safe='')
        endpoint = f'{self.base_url}/models/{model_path}:generateContent'
        body = json.dumps(self._build_payload(request)).encode('utf-8')
        http_request = Request(
            url=endpoint,
            data=body,
            headers={
                'Content-Type': 'application/json',
                'x-goog-api-key': self._api_key,
            },
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
                'O Google AI excedeu o tempo limite de resposta'
            ) from error
        except URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise LLMProviderTimeoutError(
                    'O Google AI excedeu o tempo limite de resposta'
                ) from error
            raise LLMProviderUnavailableError(
                'Nao foi possivel conectar ao Google AI'
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
                'O Google AI recusou a autenticacao'
            ) from error

        if error.code in (408, 504):
            raise LLMProviderTimeoutError(
                'O Google AI excedeu o tempo limite de resposta'
            ) from error

        if error.code == 404:
            raise LLMProviderUnavailableError(
                'O modelo solicitado nao foi encontrado no Google AI'
            ) from error

        if error.code == 429 or error.code >= 500:
            raise LLMProviderUnavailableError(
                f'O Google AI esta indisponivel: HTTP {error.code}'
            ) from error

        raise LLMProviderError(
            f'O Google AI recusou a requisicao: HTTP {error.code}'
        ) from error

    def _parse_response(
        self,
        response_body: str,
        requested_model: str,
        latency_ms: float,
    ) -> LLMResponse:
        try:
            data = json.loads(response_body)
            candidate = data['candidates'][0]
            parts = candidate['content']['parts']
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise LLMProviderInvalidResponseError(
                'O Google AI retornou uma resposta invalida'
            ) from error

        text_parts = [
            part['text']
            for part in parts
            if isinstance(part, dict) and isinstance(part.get('text'), str)
        ]
        content = ''.join(text_parts).strip()

        if not content:
            raise LLMProviderInvalidResponseError(
                'O Google AI retornou conteudo vazio ou invalido'
            )

        usage = data.get('usageMetadata', {})
        if not isinstance(usage, dict):
            raise LLMProviderInvalidResponseError(
                'O Google AI retornou metricas de uso invalidas'
            )

        model = data.get('modelVersion', requested_model)
        input_tokens = usage.get('promptTokenCount')
        output_tokens = usage.get('candidatesTokenCount')
        finish_reason = candidate.get('finishReason')

        if not isinstance(model, str) or not model.strip():
            raise LLMProviderInvalidResponseError(
                'O Google AI nao informou um modelo valido'
            )

        if input_tokens is not None and not isinstance(input_tokens, int):
            raise LLMProviderInvalidResponseError(
                'O Google AI retornou input_tokens invalido'
            )

        if output_tokens is not None and not isinstance(output_tokens, int):
            raise LLMProviderInvalidResponseError(
                'O Google AI retornou output_tokens invalido'
            )

        if finish_reason is not None and not isinstance(finish_reason, str):
            raise LLMProviderInvalidResponseError(
                'O Google AI retornou finish_reason invalido'
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
