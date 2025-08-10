#!/usr/bin/env python3
"""
TwitchIO stream notifier with Telegram notifications.
Sends messages to a Telegram group when the monitored streamer goes live.
"""
import asyncio
import os
import subprocess
import datetime
import twitchio
from twitchio import eventsub
from twitchio.ext import commands
import telegram
from telegram.error import TelegramError


class TelegramStreamNotifier(commands.AutoBot):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        target_user_id: str,
        telegram_token: str,
        telegram_chat_id: str,
        bot_id: str = None,
    ):
        self.target_user_id = target_user_id
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id

        # Initialize Telegram bot
        self.telegram_bot = telegram.Bot(token=telegram_token)

        # Base subscriptions
        subs = [
            eventsub.StreamOnlineSubscription(broadcaster_user_id=target_user_id),
            eventsub.StreamOfflineSubscription(broadcaster_user_id=target_user_id),
        ]

        # Add chat subscription if bot_id is provided
        if bot_id:
            subs.append(
                eventsub.ChatMessageSubscription(
                    broadcaster_user_id=target_user_id, user_id=bot_id
                )
            )
            print(f"Chat monitoring enabled with bot ID: {bot_id}")
        else:
            print("Chat monitoring disabled (no bot ID provided)")

        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id or "",
            prefix="!",
            subscriptions=subs,
        )
        self.chat_enabled = bool(bot_id)

    async def send_telegram_message(self, message: str, parse_mode: str = None):
        """Send a message to the Telegram group"""
        try:
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
            print(f"[TELEGRAM] Message sent successfully")
        except TelegramError as e:
            print(f"[TELEGRAM] Failed to send message: {e}")
        except Exception as e:
            print(f"[TELEGRAM] Unexpected error: {e}")

    async def event_stream_online(self, payload: twitchio.StreamOnline):
        """Handle stream online event"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        streamer_name = payload.broadcaster.display_name
        print(f"[{timestamp}] [LIVE] {streamer_name} started streaming!")

        # Get stream details if available
        title = getattr(payload, "title", "Stream")
        category = getattr(payload, "category_name", "")

        # Build Telegram message
        telegram_message = f"🔴 *{streamer_name} is LIVE!*\n\n"
        telegram_message += f"📺 {title}\n"
        if category:
            telegram_message += f"🎮 Playing: {category}\n"
        telegram_message += f"🔗 https://twitch.tv/{payload.broadcaster.name}"

        # Send to Telegram
        await self.send_telegram_message(telegram_message, parse_mode="Markdown")

        # Also send desktop notification
        notification_body = title
        if category:
            notification_body += f"\nPlaying: {category}"

        try:
            subprocess.run(
                [
                    "notify-send",
                    "-u",
                    "critical",
                    "-i",
                    "video-display",
                    f"{streamer_name} is LIVE!",
                    notification_body,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to send desktop notification: {e}")

    async def event_stream_offline(self, payload: twitchio.StreamOffline):
        """Handle stream offline event"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        streamer_name = payload.broadcaster.display_name
        print(f"[{timestamp}] [OFFLINE] {streamer_name} went offline")

        # Optional: Send offline notification to Telegram
        # Uncomment if you want offline notifications too:
        # offline_message = f"⚫ {streamer_name} went offline"
        # await self.send_telegram_message(offline_message)

    async def event_message(self, payload: twitchio.ChatMessage):
        """Handle chat messages"""
        if not self.chat_enabled:
            return

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

    async def event_ready(self):
        """Called when bot is ready"""
        print(f"Stream notifier ready! Monitoring user ID: {self.target_user_id}")
        print(
            f"Telegram notifications will be sent to chat ID: {self.telegram_chat_id}"
        )
        print("Waiting for stream events... (Press Ctrl+C to stop)")

        if self.chat_enabled:
            print("Chat monitoring: ENABLED")
        else:
            print("Chat monitoring: DISABLED (set TWITCH_BOT_ID to enable)")

        # Test Telegram connection
        try:
            me = await self.telegram_bot.get_me()
            print(f"[TELEGRAM] Connected as: {me.first_name} (@{me.username})")
        except Exception as e:
            print(f"[TELEGRAM] Connection test failed: {e}")


async def main():
    # Get credentials from environment variables
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    target_user = os.getenv("TWITCH_TARGET_USER")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    bot_id = os.getenv("TWITCH_BOT_ID")  # Optional

    if not all(
        [client_id, client_secret, target_user, telegram_token, telegram_chat_id]
    ):
        print("Error: Missing required environment variables")
        print("Required:")
        print("  TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_TARGET_USER")
        print("  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
        print("Optional:")
        print("  TWITCH_BOT_ID (for chat monitoring)")
        print()
        print("Setup instructions:")
        print("1. Create a Telegram bot via @BotFather")
        print("2. Add the bot to your group")
        print("3. Get the group chat ID (use @userinfobot)")
        return

    print(f"Starting Telegram-enabled stream notifier for user ID: {target_user}")

    try:
        async with TelegramStreamNotifier(
            client_id,
            client_secret,
            target_user,
            telegram_token,
            telegram_chat_id,
            bot_id,
        ) as bot:
            await bot.start()
    except KeyboardInterrupt:
        print("\nShutting down stream notifier...")


if __name__ == "__main__":
    asyncio.run(main())
