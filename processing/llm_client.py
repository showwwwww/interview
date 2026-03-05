"""OpenAI API wrapper with retry logic and token validation."""

from __future__ import annotations

import time

import tiktoken
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)


from config import MAX_RETRIES, MAX_TOKENS, MODEL_NAME, OPENAI_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

# Rough context limits per model family (prompt + completion).
_MODEL_CONTEXT: dict[str, int] = {
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    "gpt-3.5-turbo": 16_385,
}


def _get_encoder():
    try:
        return tiktoken.encoding_for_model(MODEL_NAME)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._client = OpenAI(api_key=api_key or OPENAI_API_KEY)
        self._model = model or MODEL_NAME
        self._encoder = _get_encoder()

    def _count_tokens(self, text: str) -> int:
        return len(self._encoder.encode(text))

    def _context_limit(self) -> int:
        for prefix, limit in _MODEL_CONTEXT.items():
            if self._model.startswith(prefix):
                return limit
        return 8_192

    def convert(self, system_prompt: str, user_content: str) -> str:
        total_tokens = self._count_tokens(system_prompt) + self._count_tokens(user_content)
        context_limit = self._context_limit()
        # Reserve space for the completion
        if total_tokens > context_limit - 1000:
            logger.warning(
                "Prompt (%d tokens) nears context limit (%d) for model %s",
                total_tokens, context_limit, self._model,
            )

        return self._call_with_retry(system_prompt, user_content)

    def _call_with_retry(self, system_prompt: str, user_content: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                )
                return response.choices[0].message.content or ""
            except AuthenticationError as exc:
                raise RuntimeError(
                    "Invalid OpenAI API key. Check your .env file and ensure "
                    "OPENAI_API_KEY is set to a valid key."
                ) from exc
            except RateLimitError as exc:
                if "insufficient_quota" in str(exc):
                    raise RuntimeError(
                        "OpenAI quota exceeded. Check your plan and billing "
                        "details at https://platform.openai.com/account/billing"
                    ) from exc
                wait = 2 ** (attempt - 1)
                logger.warning(
                    "Rate limited (attempt %d/%d): %s — retrying in %ds",
                    attempt, MAX_RETRIES, exc, wait,
                )
                last_error = exc
                time.sleep(wait)
            except (APIConnectionError, APITimeoutError) as exc:
                wait = 2 ** (attempt - 1)
                logger.warning(
                    "API error (attempt %d/%d): %s — retrying in %ds",
                    attempt, MAX_RETRIES, exc, wait,
                )
                last_error = exc
                time.sleep(wait)
        raise RuntimeError(
            f"LLM API failed after {MAX_RETRIES} retries"
        ) from last_error
