"""Broadcast stream notification command implementation"""

import asyncio
from typing import Optional

import twitchio

from ..core.config import load_config
from ..core.twitch import BaseTwitchNotifier
from ..telegram.broadcast import BroadcastNotifier


class BroadcastStreamNotifier(BaseTwitchNotifier):
    """Broadcast stream notifier combining Twitch monitoring with multi-chat Telegram broadcasting"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        target_user_id: str,
        telegram_token: str,
        bot_id: Optional[str] = None,
    ):
        super().__init__(client_id, client_secret, target_user_id, bot_id)
        self.telegram = BroadcastNotifier(telegram_token, target_user_id)

    async def on_ready(self):
        """Initialize Telegram connection and setup handlers"""
        await self.telegram.test_connection()
        await self.telegram.setup_handlers()
        print(f"[TELEGRAM] Registered chats: {self.telegram.registered_chat_count}")

    async def on_stream_online(
        self, payload: twitchio.StreamOnline, title: str, category: str
    ):
        """Broadcast stream online notification to all registered chats"""
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

    async def cleanup(self):
        """Clean shutdown of Telegram handlers"""
        await self.telegram.cleanup()


async def run_broadcast():
    """Main entry point for broadcast command"""
    config = load_config()

    notifier = BroadcastStreamNotifier(
        client_id=config["TWITCH_CLIENT_ID"],
        client_secret=config["TWITCH_CLIENT_SECRET"],
        target_user_id=config["TWITCH_TARGET_USER"],
        telegram_token=config["TELEGRAM_BOT_TOKEN"],
        bot_id=config.get("TWITCH_BOT_ID"),
    )

    try:
        async with notifier:
            await notifier.start()
    except KeyboardInterrupt:
        print("\nShutting down broadcast stream notifier...")
    finally:
        await notifier.cleanup()
