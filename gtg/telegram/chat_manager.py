"""Telegram chat persistence management"""

import datetime
import json
from typing import Set, Optional


class ChatManager:
    """Manages persistent storage of Telegram chat IDs"""

    def __init__(self, chats_file: str = "telegram_chats.json"):
        self.chats_file = chats_file
        self._chats: Set[int] = set()

    def load_chats(self) -> Set[int]:
        """Load known chat IDs from file"""
        try:
            with open(self.chats_file, "r") as f:
                data = json.load(f)
                self._chats = set(data.get("chat_ids", []))
                return self._chats.copy()
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
                        "chat_ids": list(self._chats),
                        "last_updated": datetime.datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            print(f"[ERROR] Failed to save chats: {e}")

    def add_chat(self, chat_id: int, chat_title: Optional[str] = None) -> bool:
        """Add a new chat to the list. Returns True if chat was added (new)."""
        if chat_id not in self._chats:
            self._chats.add(chat_id)
            self.save_chats()
            print(f"[TELEGRAM] Added new chat: {chat_id} ({chat_title or 'Unknown'})")
            return True
        return False

    def remove_chat(self, chat_id: int):
        """Remove a chat from the list"""
        if chat_id in self._chats:
            self._chats.discard(chat_id)
            self.save_chats()

    def remove_invalid_chats(self, invalid_chat_ids: Set[int]):
        """Remove multiple invalid chats at once"""
        if invalid_chat_ids:
            self._chats -= invalid_chat_ids
            self.save_chats()

    @property
    def chats(self) -> Set[int]:
        """Get current set of chat IDs"""
        return self._chats.copy()

    @property
    def count(self) -> int:
        """Get number of registered chats"""
        return len(self._chats)
