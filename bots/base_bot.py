"""
matrix-agent-room: Base Bot Framework
Async Matrix bot using matrix-nio that listens for @mentions
and routes messages to configured AI backends.
"""

import asyncio
import logging
import os
import time
from typing import Optional

import yaml
from nio import (
    AsyncClient,
    AsyncClientConfig,
    LoginResponse,
    MatrixRoom,
    RoomMessageText,
    SyncResponse,
)

from ollama_bot import OllamaBackend
from openai_bot import OpenAIBackend

logger = logging.getLogger("matrix-agent-room")


class RateLimiter:
    """Simple token-bucket rate limiter per user."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        if user_id not in self._requests:
            self._requests[user_id] = []

        # Clean old entries
        self._requests[user_id] = [
            t for t in self._requests[user_id]
            if now - t < self.window_seconds
        ]

        if len(self._requests[user_id]) >= self.max_requests:
            return False

        self._requests[user_id].append(now)
        return True


class AgentBot:
    """A single AI agent bot instance connected to Matrix."""

    def __init__(self, model_config: dict, homeserver_url: str):
        self.name = model_config["name"]
        self.display_name = model_config.get("display_name", self.name)
        self.matrix_user = model_config["matrix_user"]
        self.password = model_config.get("password", "")
        self.backend_type = model_config["backend"]
        self.model = model_config.get("model", "")
        self.system_prompt = model_config.get(
            "system_prompt", f"You are {self.display_name}, a helpful AI assistant."
        )
        self.api_url = model_config.get("api_url", "")
        self.api_key = model_config.get("api_key", "")
        self.max_tokens = model_config.get("max_tokens", 2048)
        self.temperature = model_config.get("temperature", 0.7)

        self.homeserver_url = homeserver_url
        self.client: Optional[AsyncClient] = None
        self.backend = self._create_backend()

    def _create_backend(self):
        """Create the appropriate backend handler."""
        if self.backend_type == "ollama":
            return OllamaBackend(
                api_url=self.api_url,
                model=self.model,
                system_prompt=self.system_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        elif self.backend_type in ("openai", "anthropic", "custom"):
            return OpenAIBackend(
                api_url=self.api_url,
                api_key=self.api_key,
                model=self.model,
                system_prompt=self.system_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        else:
            raise ValueError(f"Unknown backend type: {self.backend_type}")

    async def login(self) -> bool:
        """Connect and authenticate with the Matrix homeserver."""
        config = AsyncClientConfig(
            max_limit_exceeded=0,
            max_timeouts=0,
        )
        self.client = AsyncClient(
            self.homeserver_url,
            self.matrix_user,
            config=config,
        )

        response = await self.client.login(self.password)
        if isinstance(response, LoginResponse):
            logger.info(f"[{self.name}] Logged in as {self.matrix_user}")
            # Set display name
            await self.client.set_displayname(self.display_name)
            return True
        else:
            logger.error(f"[{self.name}] Login failed: {response}")
            return False

    async def generate_response(self, message: str, sender: str) -> str:
        """Generate a response using the configured backend."""
        try:
            return await self.backend.chat(message, sender)
        except Exception as e:
            logger.error(f"[{self.name}] Backend error: {e}")
            return f"⚠️ Sorry, I encountered an error: {type(e).__name__}"

    async def close(self):
        """Clean up the client connection."""
        if self.client:
            await self.client.close()


class BotOrchestrator:
    """
    Manages multiple AgentBot instances.
    Listens for messages, routes @mentions to the right bot.
    """

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.homeserver_url = self.config["homeserver"]["url"]
        self.bots: dict[str, AgentBot] = {}
        self.mention_only = self.config.get("triggers", {}).get("mention_only", True)
        self.allow_dm = self.config.get("triggers", {}).get("allow_dm", True)
        self.rate_limiter = RateLimiter(
            max_requests=self.config.get("rate_limit", {}).get("max_requests", 10),
            window_seconds=self.config.get("rate_limit", {}).get("window_seconds", 60),
        )
        # Track processed events to avoid duplicates
        self._processed_events: set[str] = set()
        # Listener client (we use the first bot's client to sync)
        self._listener_client: Optional[AsyncClient] = None

    @staticmethod
    def _load_config(path: str) -> dict:
        """Load and validate the YAML config file."""
        with open(path, "r") as f:
            config = yaml.safe_load(f)

        if "homeserver" not in config:
            raise ValueError("Config missing 'homeserver' section")
        if "models" not in config or not config["models"]:
            raise ValueError("Config missing 'models' section or no models defined")

        return config

    async def start(self):
        """Initialize and start all bots."""
        logger.info("Starting matrix-agent-room orchestrator...")

        # Resolve environment variables in API keys
        for model_conf in self.config["models"]:
            if "api_key_env" in model_conf:
                env_var = model_conf["api_key_env"]
                model_conf["api_key"] = os.environ.get(env_var, "")
                if not model_conf["api_key"]:
                    logger.warning(
                        f"[{model_conf['name']}] Environment variable {env_var} not set"
                    )
            if "password_env" in model_conf:
                env_var = model_conf["password_env"]
                model_conf["password"] = os.environ.get(env_var, "")

        # Create and login all bots
        for model_conf in self.config["models"]:
            bot = AgentBot(model_conf, self.homeserver_url)
            if await bot.login():
                self.bots[model_conf["name"]] = bot
                # Also index by matrix user ID for mention matching
                self.bots[model_conf["matrix_user"]] = bot
            else:
                logger.error(f"Failed to start bot: {model_conf['name']}")

        if not self.bots:
            logger.error("No bots started successfully. Exiting.")
            return

        # Use first bot as the listener
        first_bot = next(
            b for name, b in self.bots.items()
            if not name.startswith("@")
        )
        self._listener_client = first_bot.client

        logger.info(
            f"Started {len(self.config['models'])} bot(s). Listening for messages..."
        )

        # Add message callback to each bot's client
        for name, bot in self.bots.items():
            if not name.startswith("@"):
                bot.client.add_event_callback(
                    self._make_callback(bot), RoomMessageText
                )

        # Sync all bots concurrently
        await asyncio.gather(
            *[
                bot.client.sync_forever(timeout=30000, full_state=True)
                for name, bot in self.bots.items()
                if not name.startswith("@")
            ]
        )

    def _make_callback(self, listening_bot: AgentBot):
        """Create a message callback bound to a specific bot."""

        async def callback(room: MatrixRoom, event: RoomMessageText):
            # Skip our own messages
            if event.sender == listening_bot.matrix_user:
                return

            # Skip already processed events
            if event.event_id in self._processed_events:
                return
            self._processed_events.add(event.event_id)

            # Trim processed events set to prevent memory growth
            if len(self._processed_events) > 10000:
                self._processed_events = set(
                    list(self._processed_events)[-5000:]
                )

            # Skip old messages (only process messages from the last 30 seconds)
            if hasattr(event, "server_timestamp"):
                age_ms = int(time.time() * 1000) - event.server_timestamp
                if age_ms > 30000:
                    return

            message = event.body
            sender = event.sender

            # Rate limiting
            if not self.rate_limiter.is_allowed(sender):
                logger.warning(f"Rate limited: {sender}")
                return

            # Check if this bot is mentioned
            is_mentioned = (
                f"@{listening_bot.name}" in message.lower()
                or listening_bot.matrix_user in message
            )

            is_dm = len(room.users) <= 2

            if self.mention_only and not is_mentioned and not (self.allow_dm and is_dm):
                return

            logger.info(
                f"[{listening_bot.name}] Message from {sender} in {room.display_name}: "
                f"{message[:100]}..."
            )

            # Send typing indicator
            await listening_bot.client.room_typing(
                room.room_id, typing_state=True, timeout=30000
            )

            # Generate response
            # Strip the mention from the message for cleaner prompts
            clean_message = message
            for mention in [f"@{listening_bot.name}", listening_bot.matrix_user]:
                clean_message = clean_message.replace(mention, "").strip()

            response = await listening_bot.generate_response(clean_message, sender)

            # Stop typing indicator
            await listening_bot.client.room_typing(
                room.room_id, typing_state=False
            )

            # Send response
            await listening_bot.client.room_send(
                room.room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": response,
                    "format": "org.matrix.custom.html",
                    "formatted_body": response,
                },
            )

            logger.info(f"[{listening_bot.name}] Responded ({len(response)} chars)")

        return callback

    async def stop(self):
        """Gracefully shut down all bots."""
        logger.info("Shutting down...")
        for name, bot in self.bots.items():
            if not name.startswith("@"):
                await bot.close()
        logger.info("All bots stopped.")


async def main():
    """Entry point."""
    logging.basicConfig(
        level=getattr(logging, os.environ.get("BOT_LOG_LEVEL", "INFO")),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    config_path = os.environ.get("BOT_CONFIG", "/app/config.yaml")

    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        logger.error("Copy config.yaml.example to config.yaml and edit it.")
        return

    orchestrator = BotOrchestrator(config_path)

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        pass
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
