"""Abstract Telegram notification interface"""

from abc import ABC, abstractmethod
from typing import Optional

import telegram
from telegram.error import TelegramError
from telegram.helpers import escape_markdown


class TelegramNotifier(ABC):
    """Abstract base class for Telegram notifications"""

    def __init__(self, token: str):
        self.token = token
        self.bot = telegram.Bot(token=token)

    async def test_connection(self) -> bool:
        """Test Telegram bot connection and print status"""
        try:
            me = await self.bot.get_me()
            print(f"[TELEGRAM] Connected as: {me.first_name} (@{me.username})")
            return True
        except Exception as e:
            print(f"[TELEGRAM] Connection test failed: {e}")
            return False

    @abstractmethod
    async def send_message(
        self, message: str, parse_mode: Optional[str] = None
    ) -> bool:
        """Send message to configured chat(s). Returns True if successful."""
        pass

    def format_stream_message(
        self, streamer_name: str, title: str, category: str, twitch_url: str
    ) -> str:
        """Format stream online message with proper Telegram markdown escaping"""
        escaped_title = escape_markdown(title)
        escaped_category = escape_markdown(category) if category else ""

        return f"""💊 {streamer_name} is LIVE 💊
{escaped_title}/{escaped_category if escaped_category else ""}
{twitch_url}""".strip()

    async def handle_telegram_error(
        self, error: TelegramError, chat_id: Optional[int] = None
    ) -> bool:
        """Handle Telegram errors and return True if chat should be removed"""
        error_msg = str(error).lower()
        if "chat not found" in error_msg or "bot was blocked" in error_msg:
            if chat_id:
                print(f"[TELEGRAM] Removed invalid chat {chat_id}: {error}")
            return True
        else:
            if chat_id:
                print(f"[TELEGRAM] Failed to send to {chat_id}: {error}")
            else:
                print(f"[TELEGRAM] Failed to send message: {error}")
            return False
