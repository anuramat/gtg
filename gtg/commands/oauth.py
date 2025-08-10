"""OAuth stream notification command implementation"""

import asyncio
import datetime
import subprocess
from typing import Optional

import twitchio
from twitchio import eventsub
from twitchio.ext import commands

from ..core.config import load_config
from ..telegram.single import SingleChatNotifier
from ..telegram.broadcast import BroadcastNotifier


class OAuthStreamNotifier(commands.AutoBot):
    """OAuth-based stream notifier with web authentication flow"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        bot_id: str,
        telegram_token: str,
        telegram_chat_id: Optional[str] = None,
    ):
        # Start with empty subscriptions - they'll be added when users authenticate
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            prefix="!",
            subscriptions=[],
        )

        # Setup Telegram notifier based on whether chat_id is provided
        if telegram_chat_id:
            self.telegram = SingleChatNotifier(telegram_token, telegram_chat_id)
            self.use_broadcast = False
        else:
            # For broadcast, we need a dummy target_user_id - will be updated during OAuth
            self.telegram = BroadcastNotifier(telegram_token, "dummy")
            self.use_broadcast = True

    async def event_ready(self):
        """Called when bot is ready"""
        print("OAuth stream notifier is ready!")
        print("To monitor a channel:")
        print("1. Visit http://localhost:4343/oauth?scopes=channel:bot")
        print("2. Log in as the streamer you want to monitor")
        print("3. The bot will automatically subscribe to their events")

        # Initialize Telegram
        await self.telegram.test_connection()
        if self.use_broadcast:
            await self.telegram.setup_handlers()
            print(f"[TELEGRAM] Registered chats: {self.telegram.registered_chat_count}")

    async def event_oauth_authorized(
        self, payload: twitchio.authentication.UserTokenPayload
    ):
        """Called when a user authorizes the bot"""
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        print(f"User {payload.user_id} authorized! Setting up monitoring...")

        # Subscribe to events for this user
        subs = [
            eventsub.StreamOnlineSubscription(broadcaster_user_id=payload.user_id),
            eventsub.StreamOfflineSubscription(broadcaster_user_id=payload.user_id),
            eventsub.ChatMessageSubscription(
                broadcaster_user_id=payload.user_id, user_id=self.bot_id
            ),
        ]

        resp = await self.multi_subscribe(subs)
        if resp.errors:
            print(f"Failed to subscribe to some events: {resp.errors}")
        else:
            print(f"Successfully monitoring user {payload.user_id}")

    async def event_stream_online(self, payload: twitchio.StreamOnline):
        """Handle stream online event"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        streamer_name = payload.broadcaster.display_name
        print(f"[{timestamp}] [LIVE] {streamer_name} started streaming!")

        # Send desktop notification
        title = getattr(payload, "title", "Stream")
        category = getattr(payload, "category_name", "")
        self._send_desktop_notification(streamer_name, title, category)

        # Send Telegram notification
        twitch_url = f"https://twitch.tv/{payload.broadcaster.name}"
        message = self.telegram.format_stream_message(
            streamer_name, title, category, twitch_url
        )
        await self.telegram.send_message(message, "MarkdownV2")

    async def event_stream_offline(self, payload: twitchio.StreamOffline):
        """Handle stream offline event"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        streamer_name = payload.broadcaster.display_name
        print(f"[{timestamp}] [OFFLINE] {streamer_name} went offline")

    async def event_message(self, payload: twitchio.ChatMessage):
        """Handle chat messages"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # Determine user type
        if payload.chatter.broadcaster:
            prefix = "[STREAMER]"
        elif payload.chatter.moderator:
            prefix = "[MOD]"
        elif payload.chatter.subscriber:
            prefix = "[SUB]"
        else:
            prefix = "[CHAT]"

        print(f"[{timestamp}] {prefix} {payload.chatter.display_name}: {payload.text}")

    def _send_desktop_notification(self, streamer_name: str, title: str, category: str):
        """Send desktop notification using notify-send"""
        body = title
        if category:
            body += f"\\nPlaying: {category}"

        try:
            subprocess.run(
                [
                    "notify-send",
                    "-u",
                    "critical",
                    "-i",
                    "video-display",
                    f"{streamer_name} is LIVE!",
                    body,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to send desktop notification: {e}")

    async def cleanup(self):
        """Clean shutdown"""
        if hasattr(self.telegram, "cleanup"):
            await self.telegram.cleanup()


async def run_oauth():
    """Main entry point for OAuth command"""
    config = load_config()

    bot_id = config.get("TWITCH_BOT_ID")
    if not bot_id:
        print("Error: TWITCH_BOT_ID is required for OAuth authentication")
        print("Setup instructions:")
        print("1. Create a bot Twitch account")
        print("2. Get the bot's user ID using: gtg get-user-id <bot_username>")
        print("3. Create a Twitch app at https://dev.twitch.tv/console/apps")
        print("4. Set redirect URI to: http://localhost:4343/oauth/callback")
        return

    print(f"Starting OAuth stream notifier with bot ID: {bot_id}")

    notifier = OAuthStreamNotifier(
        client_id=config["TWITCH_CLIENT_ID"],
        client_secret=config["TWITCH_CLIENT_SECRET"],
        bot_id=bot_id,
        telegram_token=config["TELEGRAM_BOT_TOKEN"],
        telegram_chat_id=config.get("TELEGRAM_CHAT_ID"),
    )

    try:
        async with notifier:
            await notifier.start()
    except KeyboardInterrupt:
        print("\nShutting down OAuth stream notifier...")
    finally:
        await notifier.cleanup()
