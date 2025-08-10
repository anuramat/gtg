"""Single chat stream notification command implementation"""

import asyncio
from typing import Optional

import twitchio

from ..core.config import load_config
from ..core.twitch import BaseTwitchNotifier
from ..telegram.single import SingleChatNotifier


class SingleChatStreamNotifier(BaseTwitchNotifier):
    """Single chat stream notifier combining Twitch monitoring with single Telegram chat"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        target_user_id: str,
        telegram_token: str,
        telegram_chat_id: str,
        bot_id: Optional[str] = None,
    ):
        super().__init__(client_id, client_secret, target_user_id, bot_id)
        self.telegram = SingleChatNotifier(telegram_token, telegram_chat_id)

    async def on_ready(self):
        """Initialize Telegram connection"""
        await self.telegram.test_connection()

    async def on_stream_online(
        self, payload: twitchio.StreamOnline, title: str, category: str
    ):
        """Send stream online notification to single chat"""
        streamer_name = payload.broadcaster.display_name
        twitch_url = f"https://twitch.tv/{payload.broadcaster.name}"
        message = self.telegram.format_stream_message(
            streamer_name, title, category, twitch_url
        )
        await self.telegram.send_message(message, "MarkdownV2")

    async def on_stream_offline(self, payload: twitchio.StreamOffline):
        """Handle stream offline - currently no Telegram notification"""
        pass

    async def on_chat_message(self, payload: twitchio.ChatMessage):
        """Handle chat message - currently no additional processing"""
        pass


async def run_single_chat():
    """Main entry point for single chat command"""
    config = load_config()

    notifier = SingleChatStreamNotifier(
        client_id=config["TWITCH_CLIENT_ID"],
        client_secret=config["TWITCH_CLIENT_SECRET"],
        target_user_id=config["TWITCH_TARGET_USER"],
        telegram_token=config["TELEGRAM_BOT_TOKEN"],
        telegram_chat_id=config["TELEGRAM_CHAT_ID"],
        bot_id=config.get("TWITCH_BOT_ID"),
    )

    try:
        async with notifier:
            await notifier.start()
    except KeyboardInterrupt:
        print("\nShutting down single chat stream notifier...")
