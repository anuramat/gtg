#!/usr/bin/env python3
"""
GTG CLI Usage Examples
This demonstrates how to use the new GTG command-line interface.
"""

# =============================================================================
# CLI USAGE EXAMPLES
# =============================================================================

# 1. Convert Twitch username to user ID (needed for TWITCH_TARGET_USER)
"""
export TWITCH_CLIENT_ID="your_client_id"
export TWITCH_CLIENT_SECRET="your_client_secret"

python gtg.py get-user-id username
# OR
python -m gtg get-user-id username
"""

# 2. Run broadcast notifier (recommended - auto-discovers all chats)
"""
export TWITCH_CLIENT_ID="your_client_id"
export TWITCH_CLIENT_SECRET="your_client_secret"
export TWITCH_TARGET_USER="123456789"  # Use get-user-id to find this
export TELEGRAM_BOT_TOKEN="your_bot_token"
# Optional: export TWITCH_BOT_ID="your_bot_user_id"  # Enables chat monitoring

python gtg.py broadcast
# OR
python -m gtg broadcast
"""


# =============================================================================
# SETUP INSTRUCTIONS
# =============================================================================

"""
1. Twitch App Setup:
   - Go to https://dev.twitch.tv/console/apps
   - Create a new app with OAuth redirect URL: http://localhost:8080/callback
   - Note your Client ID and Client Secret

2. Telegram Bot Setup:
   - Message @BotFather on Telegram
   - Create a new bot with /newbot
   - Note your bot token
   - Add the bot to your Telegram groups/chats

3. Environment Variables:
   - Copy .env.example to .env and fill in your credentials
   - Or export the variables in your shell

4. Usage:
   - Use broadcast mode for multiple chats (recommended)
   - Use get-user-id to convert Twitch usernames to user IDs
"""

# =============================================================================
# MIGRATION FROM OLD SCRIPTS
# =============================================================================

# Old way:
# python stream_notifier_broadcast.py
# python get_user_id.py username

# New way:
# python gtg.py broadcast
# python gtg.py get-user-id username

# =============================================================================
# PROGRAMMATIC API EXAMPLES (for developers)
# =============================================================================

import asyncio
from typing import Optional

import twitchio
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from gtg.core import BaseTwitchNotifier
from gtg.telegram import TelegramNotifier, ChatManager


class BroadcastTelegramNotifier(TelegramNotifier):
    """Telegram notifier that broadcasts to all registered chats"""

    def __init__(self, token: str, chats_file: str = "telegram_chats.json"):
        super().__init__(token)
        self.chat_manager = ChatManager(chats_file)
        self.chat_manager.load_chats()
        self.telegram_app: Optional[Application] = None

    async def send_message(
        self, message: str, parse_mode: Optional[str] = None
    ) -> bool:
        """Broadcast message to all registered chats"""
        chats = self.chat_manager.chats
        if not chats:
            print(
                "[TELEGRAM] No registered chats - send /start to the bot in your groups"
            )
            return False

        success_count = 0
        invalid_chats = set()

        for chat_id in chats:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True,
                )
                success_count += 1
            except Exception as e:
                if self.handle_telegram_error(e, chat_id):
                    invalid_chats.add(chat_id)

        self.chat_manager.remove_invalid_chats(invalid_chats)
        print(f"[TELEGRAM] Broadcast: {success_count}/{len(chats)} chats")
        return success_count > 0

    async def setup_handlers(self):
        """Set up Telegram command handlers for chat discovery"""
        self.telegram_app = Application.builder().token(self.token).build()

        async def start_command(update, context):
            chat_id = update.effective_chat.id
            chat_title = getattr(update.effective_chat, "title", "Private Chat")
            self.chat_manager.add_chat(chat_id, chat_title)
            await update.message.reply_text(
                f"✅ Stream notifications enabled!\\nChat ID: {chat_id}"
            )

        async def auto_register(update, context):
            if update.effective_chat.type in ["group", "supergroup"]:
                self.chat_manager.add_chat(
                    update.effective_chat.id, update.effective_chat.title
                )

        self.telegram_app.add_handler(CommandHandler("start", start_command))
        self.telegram_app.add_handler(MessageHandler(filters.ALL, auto_register))

        await self.telegram_app.initialize()
        await self.telegram_app.start()
        asyncio.create_task(self.telegram_app.updater.start_polling())


class ExampleStreamNotifier(BaseTwitchNotifier):
    """Example implementation combining Twitch monitoring with Telegram broadcast"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        target_user_id: str,
        telegram_token: str,
        bot_id: Optional[str] = None,
    ):
        super().__init__(client_id, client_secret, target_user_id, bot_id)
        self.telegram = BroadcastTelegramNotifier(telegram_token)

    async def on_ready(self):
        """Called when bot is ready"""
        print(f"Registered Telegram chats: {self.telegram.chat_manager.count}")
        await self.telegram.test_connection()
        await self.telegram.setup_handlers()
        print("Example notifier ready!")

    async def on_stream_online(
        self, payload: twitchio.StreamOnline, title: str, category: str
    ):
        """Send Telegram notification when stream goes online"""
        streamer_name = payload.broadcaster.display_name
        twitch_url = f"https://twitch.tv/{payload.broadcaster.name}"
        message = self.telegram.format_stream_message(
            streamer_name, title, category, twitch_url
        )
        await self.telegram.send_message(message, parse_mode="MarkdownV2")

    async def on_stream_offline(self, payload: twitchio.StreamOffline):
        """Handle stream offline - no notification by default"""
        pass

    async def on_chat_message(self, payload: twitchio.ChatMessage):
        """Handle chat messages - just logged by parent class"""
        pass

    async def close(self):
        """Clean shutdown"""
        if self.telegram.telegram_app:
            await self.telegram.telegram_app.stop()
        await super().close()


# This shows how clean the programmatic usage would be:
# notifier = ExampleStreamNotifier(client_id, client_secret, target_user, telegram_token, bot_id)
# async with notifier:
#     await notifier.start()
