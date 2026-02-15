"""
OpenAI-compatible backend integration for matrix-agent-room.
Works with OpenAI, Anthropic (via proxy), LM Studio, vLLM,
text-generation-webui, LocalAI, and any OpenAI-format endpoint.
"""

import logging
import os
from typing import Optional

import aiohttp

logger = logging.getLogger("matrix-agent-room.openai")


class OpenAIBackend:
    """OpenAI-compatible API integration for chat completions."""

    def __init__(
        self,
        api_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4",
        system_prompt: str = "You are a helpful AI assistant.",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=120)
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._session = aiohttp.ClientSession(
                timeout=timeout, headers=headers
            )
        return self._session

    def _build_messages(
        self, message: str, sender: str, history: list[dict]
    ) -> list[dict]:
        """Build the messages array with conversation history.

        History entries are dicts with keys: sender, message, timestamp.
        Bot's own messages become role='assistant'; all others become role='user'.
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        # Append conversation history (excluding the current message which is last)
        for entry in history[:-1] if history else []:
            content = f"{entry['sender']}: {entry['message']}"
            messages.append({"role": "user", "content": content})

        # Current user message
        messages.append({"role": "user", "content": f"{sender}: {message}"})

        return messages

    async def chat(
        self, message: str, sender: str = "", history: Optional[list[dict]] = None
    ) -> str:
        """
        Send a chat message to an OpenAI-compatible API and return the response.

        Args:
            message: The user's message text.
            sender: Matrix user ID or display name of the sender.
            history: Recent conversation history for context replay.

        Returns:
            The model's response text.
        """
        session = await self._get_session()

        payload = {
            "model": self.model,
            "messages": self._build_messages(message, sender, history or []),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False,
        }

        endpoint = f"{self.api_url}/chat/completions"

        try:
            async with session.post(endpoint, json=payload) as resp:
                if resp.status == 401:
                    logger.error("API authentication failed — check your API key")
                    return "⚠️ Authentication failed. Check the API key configuration."

                if resp.status == 429:
                    logger.warning("Rate limited by API provider")
                    return "⚠️ Rate limited by the API provider. Try again in a moment."

                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(
                        f"API error ({resp.status}): {error_text[:200]}"
                    )
                    return f"⚠️ API returned an error (HTTP {resp.status})"

                data = await resp.json()

                # Extract response text from OpenAI-format response
                choices = data.get("choices", [])
                if not choices:
                    logger.warning("API returned no choices")
                    return "🤔 The model returned an empty response."

                response_text = choices[0].get("message", {}).get("content", "")

                if not response_text:
                    logger.warning("API returned empty content")
                    return "🤔 I generated an empty response. Try rephrasing?"

                # Log usage stats if available
                usage = data.get("usage", {})
                if usage:
                    logger.debug(
                        f"API usage: model={self.model}, "
                        f"prompt_tokens={usage.get('prompt_tokens', '?')}, "
                        f"completion_tokens={usage.get('completion_tokens', '?')}"
                    )

                return response_text

        except aiohttp.ClientConnectorError:
            logger.error(f"Cannot connect to API at {self.api_url}")
            return (
                "⚠️ Cannot reach the API server. "
                "Check the api_url in your config."
            )
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            return f"⚠️ Request to model failed: {type(e).__name__}"
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI backend: {e}")
            return f"⚠️ Unexpected error: {type(e).__name__}"

    async def list_models(self) -> list[str]:
        """List available models from the API."""
        session = await self._get_session()

        try:
            async with session.get(f"{self.api_url}/models") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [m["id"] for m in data.get("data", [])]
                return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if the API endpoint is reachable."""
        session = await self._get_session()

        try:
            async with session.get(f"{self.api_url}/models") as resp:
                return resp.status in (200, 401)  # 401 = reachable but needs auth
        except Exception:
            return False

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
