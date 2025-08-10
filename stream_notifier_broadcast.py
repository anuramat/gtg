#!/usr/bin/env python3
"""
TwitchIO stream notifier with Telegram broadcast to all known chats.
Automatically discovers and broadcasts to all chats the bot is added to.
"""
import asyncio
import os
import subprocess
import datetime
import json
import twitchio
from twitchio import eventsub
from twitchio.ext import commands
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import TelegramError


class TelegramBroadcastNotifier(commands.AutoBot):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        target_user_id: str,
        telegram_token: str,
        bot_id: str = None,
    ):
        self.target_user_id = target_user_id
        self.telegram_token = telegram_token
        self.chats_file = "telegram_chats.json"

        # Initialize Telegram bot
        self.telegram_bot = telegram.Bot(token=telegram_token)
        self.telegram_app = None
        self.known_chats = self.load_chats()

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

    def load_chats(self) -> set:
        """Load known chat IDs from file"""
        try:
            with open(self.chats_file, "r") as f:
                data = json.load(f)
                return set(data.get("chat_ids", []))
        except FileNotFoundError:
            return set()
        except json.JSONDecodeError:
            print(f"[ERROR] Corrupted {self.chats_file}, starting fresh")
            return set()

    def save_chats(self):
        """Save known chat IDs to file"""
        try:
            with open(self.chats_file, "w") as f:
                json.dump(
                    {
                        "chat_ids": list(self.known_chats),
                        "last_updated": datetime.datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            print(f"[ERROR] Failed to save chats: {e}")

    def add_chat(self, chat_id: int, chat_title: str = None):
        """Add a new chat to broadcast list"""
        if chat_id not in self.known_chats:
            self.known_chats.add(chat_id)
            self.save_chats()
            print(f"[TELEGRAM] Added new chat: {chat_id} ({chat_title or 'Unknown'})")

    async def setup_telegram_handlers(self):
        """Set up Telegram bot handlers for chat discovery"""
        self.telegram_app = Application.builder().token(self.telegram_token).build()

        # Handler for /start command - registers the chat
        async def start_command(update: Update, context):
            chat_id = update.effective_chat.id
            chat_title = getattr(update.effective_chat, "title", "Private Chat")
            self.add_chat(chat_id, chat_title)

            await update.message.reply_text(
                f"✅ Stream notifications enabled!\n"
                f"This chat will receive notifications when streams go live.\n"
                f"Chat ID: {chat_id}"
            )

        # Handler for /status command - shows current settings
        async def status_command(update: Update, context):
            chat_count = len(self.known_chats)
            await update.message.reply_text(
                f"📊 Stream Notifier Status\n"
                f"Monitoring: User ID {self.target_user_id}\n"
                f"Registered chats: {chat_count}\n"
                f"This chat ID: {update.effective_chat.id}"
            )

        # Handler for any message - auto-registers new chats
        async def auto_register(update: Update, context):
            # Only register group chats, not private chats (optional)
            if update.effective_chat.type in ["group", "supergroup"]:
                chat_id = update.effective_chat.id
                chat_title = update.effective_chat.title
                self.add_chat(chat_id, chat_title)

        # Add handlers
        self.telegram_app.add_handler(CommandHandler("start", start_command))
        self.telegram_app.add_handler(CommandHandler("status", status_command))
        self.telegram_app.add_handler(MessageHandler(filters.ALL, auto_register))

        # Start the telegram bot
        await self.telegram_app.initialize()
        await self.telegram_app.start()

        # Start polling in background
        asyncio.create_task(self.telegram_app.updater.start_polling())

    async def broadcast_message(self, message: str, parse_mode: str = None):
        """Send message to all known chats"""
        if not self.known_chats:
            print(
                "[TELEGRAM] No registered chats - send /start to the bot in your groups"
            )
            return

        success_count = 0
        failed_chats = []

        for (
            chat_id
        ) in self.known_chats.copy():  # Use copy to avoid modification during iteration
            try:
                await self.telegram_bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True,
                )
                success_count += 1
            except TelegramError as e:
                failed_chats.append(chat_id)
                if (
                    "chat not found" in str(e).lower()
                    or "bot was blocked" in str(e).lower()
                ):
                    # Remove invalid chats
                    self.known_chats.discard(chat_id)
                    print(f"[TELEGRAM] Removed invalid chat {chat_id}: {e}")
                else:
                    print(f"[TELEGRAM] Failed to send to {chat_id}: {e}")

        # Save updated chat list if any were removed
        if failed_chats:
            self.save_chats()

        print(
            f"[TELEGRAM] Broadcast complete: {success_count}/{len(self.known_chats) + len(failed_chats)} chats"
        )

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

        # Broadcast to all chats
        await self.broadcast_message(telegram_message, parse_mode="Markdown")

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

        # Optional: Send offline notification to all chats
        # Uncomment if you want offline notifications too:
        # offline_message = f"⚫ {streamer_name} went offline"
        # await self.broadcast_message(offline_message)

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
        print(f"Registered Telegram chats: {len(self.known_chats)}")
        print("Waiting for stream events... (Press Ctrl+C to stop)")

        if self.chat_enabled:
            print("Chat monitoring: ENABLED")
        else:
            print("Chat monitoring: DISABLED (set TWITCH_BOT_ID to enable)")

        # Set up Telegram handlers
        await self.setup_telegram_handlers()

        # Test Telegram connection
        try:
            me = await self.telegram_bot.get_me()
            print(f"[TELEGRAM] Connected as: {me.first_name} (@{me.username})")
            print(f"[TELEGRAM] Add bot to groups and send /start to register them")
        except Exception as e:
            print(f"[TELEGRAM] Connection test failed: {e}")

    async def close(self):
        """Clean shutdown"""
        if self.telegram_app:
            await self.telegram_app.stop()
        await super().close()


async def main():
    # Get credentials from environment variables
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    target_user = os.getenv("TWITCH_TARGET_USER")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    bot_id = os.getenv("TWITCH_BOT_ID")  # Optional

    if not all([client_id, client_secret, target_user, telegram_token]):
        print("Error: Missing required environment variables")
        print("Required:")
        print("  TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_TARGET_USER")
        print("  TELEGRAM_BOT_TOKEN")
        print("Optional:")
        print("  TWITCH_BOT_ID (for chat monitoring)")
        print()
        print("Setup instructions:")
        print("1. Create a Telegram bot via @BotFather")
        print("2. Add the bot to your groups")
        print("3. Send /start in each group to register them")
        return

    print(f"Starting broadcast stream notifier for user ID: {target_user}")

    try:
        notifier = TelegramBroadcastNotifier(
            client_id, client_secret, target_user, telegram_token, bot_id
        )
        async with notifier:
            await notifier.start()
    except KeyboardInterrupt:
        print("\nShutting down stream notifier...")


if __name__ == "__main__":
    asyncio.run(main())
