"""Single chat Telegram notification strategy"""

from typing import Optional

from telegram.error import TelegramError

from .base import TelegramNotifier


class SingleChatNotifier(TelegramNotifier):
    """Telegram notifier that sends messages to a single specified chat"""

    def __init__(self, token: str, chat_id: str):
        super().__init__(token)
        self.chat_id = chat_id

    async def send_message(
        self, message: str, parse_mode: Optional[str] = None
    ) -> bool:
        """Send message to the configured single chat"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
            print(f"[TELEGRAM] Message sent successfully")
            return True
        except TelegramError as e:
            await self.handle_telegram_error(
                e, int(self.chat_id) if self.chat_id.lstrip("-").isdigit() else None
            )
            return False
        except Exception as e:
            print(f"[TELEGRAM] Unexpected error: {e}")
            return False
