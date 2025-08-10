"""Broadcast Telegram notification strategy with chat discovery"""

import asyncio
from typing import Optional, Set

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .base import TelegramNotifier
from .chat_manager import ChatManager


class BroadcastNotifier(TelegramNotifier):
    """Telegram notifier that broadcasts to all registered chats with auto-discovery"""

    def __init__(
        self, token: str, target_user_id: str, chats_file: str = "telegram_chats.json"
    ):
        super().__init__(token)
        self.target_user_id = target_user_id
        self.chat_manager = ChatManager(chats_file)
        self.telegram_app: Optional[Application] = None
        self.chat_manager.load_chats()

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
        invalid_chats: Set[int] = set()

        for chat_id in chats:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True,
                )
                success_count += 1
            except TelegramError as e:
                if await self.handle_telegram_error(e, chat_id):
                    invalid_chats.add(chat_id)

        # Remove invalid chats
        if invalid_chats:
            self.chat_manager.remove_invalid_chats(invalid_chats)

        total_attempted = len(chats)
        print(f"[TELEGRAM] Broadcast complete: {success_count}/{total_attempted} chats")
        return success_count > 0

    async def setup_handlers(self):
        """Set up Telegram bot handlers for chat discovery"""
        self.telegram_app = Application.builder().token(self.token).build()

        async def start_command(update: Update, context):
            chat_id = update.effective_chat.id
            chat_title = getattr(update.effective_chat, "title", "Private Chat")
            self.chat_manager.add_chat(chat_id, chat_title)

            await update.message.reply_text(
                f"✅ Stream notifications enabled!\n"
                f"This chat will receive notifications when streams go live.\n"
                f"Chat ID: {chat_id}"
            )

        async def status_command(update: Update, context):
            await update.message.reply_text(
                f"📊 Stream Notifier Status\n"
                f"Monitoring: User ID {self.target_user_id}\n"
                f"Registered chats: {self.chat_manager.count}\n"
                f"This chat ID: {update.effective_chat.id}"
            )

        async def auto_register(update: Update, context):
            # Only register group chats, not private chats
            if update.effective_chat.type in ["group", "supergroup"]:
                chat_id = update.effective_chat.id
                chat_title = update.effective_chat.title
                self.chat_manager.add_chat(chat_id, chat_title)

        # Add handlers
        self.telegram_app.add_handler(CommandHandler("start", start_command))
        self.telegram_app.add_handler(CommandHandler("status", status_command))
        self.telegram_app.add_handler(MessageHandler(filters.ALL, auto_register))

        # Start the telegram bot
        await self.telegram_app.initialize()
        await self.telegram_app.start()

        # Start polling in background
        asyncio.create_task(self.telegram_app.updater.start_polling())
        print(f"[TELEGRAM] Add bot to groups and send /start to register them")

    async def cleanup(self):
        """Clean shutdown of Telegram handlers"""
        if self.telegram_app:
            await self.telegram_app.stop()

    @property
    def registered_chat_count(self) -> int:
        """Get number of registered chats"""
        return self.chat_manager.count
