"""
Ollama backend integration for matrix-agent-room.
Routes chat messages to a local Ollama instance via HTTP API.
"""

import logging
from typing import Optional

import aiohttp

logger = logging.getLogger("matrix-agent-room.ollama")


class OllamaBackend:
    """Ollama HTTP API integration for chat completions."""

    def __init__(
        self,
        api_url: str = "http://ollama:11434",
        model: str = "mistral:7b",
        system_prompt: str = "You are a helpful AI assistant.",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        self.api_url = api_url.rstrip("/")
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=120)
            self._session = aiohttp.ClientSession(timeout=timeout)
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
            # If the message was from this bot, mark as assistant
            # We compare against system_prompt to infer identity isn't reliable,
            # so we check if sender matches common bot patterns
            content = f"{entry['sender']}: {entry['message']}"
            messages.append({"role": "user", "content": content})

        # Current user message
        messages.append({"role": "user", "content": f"{sender}: {message}"})

        return messages

    async def chat(
        self, message: str, sender: str = "", history: Optional[list[dict]] = None
    ) -> str:
        """
        Send a chat message to Ollama and return the response.

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
            "stream": False,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
            },
        }

        try:
            async with session.post(
                f"{self.api_url}/api/chat", json=payload
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(
                        f"Ollama API error ({resp.status}): {error_text[:200]}"
                    )
                    return f"⚠️ Model returned an error (HTTP {resp.status})"

                data = await resp.json()
                response_text = data.get("message", {}).get("content", "")

                if not response_text:
                    logger.warning("Ollama returned empty response")
                    return "🤔 I generated an empty response. Try rephrasing?"

                logger.debug(
                    f"Ollama response: model={self.model}, "
                    f"tokens={data.get('eval_count', '?')}, "
                    f"duration={data.get('total_duration', '?')}ns"
                )

                return response_text

        except aiohttp.ClientConnectorError:
            logger.error(f"Cannot connect to Ollama at {self.api_url}")
            return (
                "⚠️ Cannot reach the Ollama server. "
                "Is it running? Check OLLAMA_URL in your config."
            )
        except aiohttp.ClientError as e:
            logger.error(f"Ollama request failed: {e}")
            return f"⚠️ Request to model failed: {type(e).__name__}"
        except Exception as e:
            logger.error(f"Unexpected error in Ollama backend: {e}")
            return f"⚠️ Unexpected error: {type(e).__name__}"

    async def list_models(self) -> list[str]:
        """List available models on the Ollama instance."""
        session = await self._get_session()

        try:
            async with session.get(f"{self.api_url}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [m["name"] for m in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if the Ollama server is reachable."""
        session = await self._get_session()

        try:
            async with session.get(f"{self.api_url}/api/tags") as resp:
                return resp.status == 200
        except Exception:
            return False

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
