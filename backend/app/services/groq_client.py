import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import logger

GROQ_API_BASE = "https://api.groq.com/openai/v1"


class GroqClientError(Exception):
    pass


class GroqClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self.temperature = temperature if temperature is not None else settings.groq_temperature
        self.max_tokens = max_tokens or settings.groq_max_tokens
        self.timeout = timeout or settings.groq_timeout
        self.max_retries = max_retries or settings.groq_max_retries
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=GROQ_API_BASE,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def complete(
        self, messages: list[dict[str, str]]
    ) -> tuple[str, dict[str, Any]]:
        if not self.api_key:
            raise GroqClientError("GROQ_API_KEY is not configured")

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                return self._do_complete(messages)
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    "Groq API timeout (attempt %d/%d): %s",
                    attempt,
                    self.max_retries + 1,
                    e,
                )
            except httpx.HTTPStatusError as e:
                last_error = e
                status = e.response.status_code
                if status in (429, 500, 502, 503, 504):
                    logger.warning(
                        "Groq API %d (attempt %d/%d): %s",
                        status,
                        attempt,
                        self.max_retries + 1,
                        e,
                    )
                else:
                    raise GroqClientError(f"Groq API error {status}: {e}") from e
            except httpx.RequestError as e:
                last_error = e
                logger.warning(
                    "Groq API request failed (attempt %d/%d): %s",
                    attempt,
                    self.max_retries + 1,
                    e,
                )

            if attempt < self.max_retries + 1:
                wait = 2 ** attempt
                logger.info("Retrying Groq API in %ds...", wait)
                time.sleep(wait)

        raise GroqClientError(
            f"Groq API failed after {self.max_retries + 1} attempts"
        ) from last_error

    def _do_complete(
        self, messages: list[dict[str, str]]
    ) -> tuple[str, dict[str, Any]]:
        client = self._get_client()
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        response = client.post("/chat/completions", json=body)
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        info = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "model": data.get("model", self.model),
        }
        return content.strip(), info

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
