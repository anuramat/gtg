"""Base Twitch notification classes using TwitchIO AutoBot"""

import datetime
import subprocess
from abc import ABC, abstractmethod
from typing import List, Optional

import twitchio
from twitchio import eventsub
from twitchio.ext import commands

from .notifications import send_desktop_notification


class BaseTwitchNotifier(commands.AutoBot, ABC):
    """Base class for Twitch stream notifiers using EventSub subscriptions"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        target_user_id: str,
        bot_id: Optional[str] = None,
    ):
        self.target_user_id = target_user_id
        self.chat_enabled = bool(bot_id)

        # Build subscriptions
        subs = [
            eventsub.StreamOnlineSubscription(broadcaster_user_id=target_user_id),
            eventsub.StreamOfflineSubscription(broadcaster_user_id=target_user_id),
        ]

        if bot_id:
            subs.append(
                eventsub.ChatMessageSubscription(
                    broadcaster_user_id=target_user_id, user_id=bot_id
                )
            )

        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id or "",
            prefix="!",
            subscriptions=subs,
        )

    async def event_ready(self):
        """Called when bot is ready - delegates to subclass"""
        print(f"Stream notifier ready! Monitoring user ID: {self.target_user_id}")
        print(f"Chat monitoring: {'ENABLED' if self.chat_enabled else 'DISABLED'}")
        await self.on_ready()

    async def event_stream_online(self, payload: twitchio.StreamOnline):
        """Handle stream online event"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        streamer_name = payload.broadcaster.display_name
        print(f"[{timestamp}] [LIVE] {streamer_name} started streaming!")

        # Get stream details
        title = getattr(payload, "title", "Stream")
        category = getattr(payload, "category_name", "")

        # Send notifications
        await self.on_stream_online(payload, title, category)
        self._send_desktop_notification(streamer_name, title, category)

    async def event_stream_offline(self, payload: twitchio.StreamOffline):
        """Handle stream offline event"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        streamer_name = payload.broadcaster.display_name
        print(f"[{timestamp}] [OFFLINE] {streamer_name} went offline")
        await self.on_stream_offline(payload)

    async def event_message(self, payload: twitchio.ChatMessage):
        """Handle chat messages"""
        if not self.chat_enabled:
            return

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = self._get_user_prefix(payload.chatter)
        display_name = payload.chatter.display_name
        message_text = payload.text

        print(f"[{timestamp}] {prefix} {display_name}: {message_text}")

        # Send desktop notification for chat messages
        title = f"{display_name} in chat"
        send_desktop_notification(title, message_text, urgency="normal")

        await self.on_chat_message(payload)

    @staticmethod
    def _get_user_prefix(chatter) -> str:
        """Get user type prefix for chat messages"""
        if chatter.broadcaster:
            return "[STREAMER]"
        elif chatter.moderator:
            return "[MOD]"
        elif chatter.subscriber:
            return "[SUB]"
        else:
            return "[CHAT]"

    def _send_desktop_notification(self, streamer_name: str, title: str, category: str):
        """Send desktop notification using notify-send"""
        body = title
        if category:
            body += f"\\nPlaying: {category}"

        send_desktop_notification(f"{streamer_name} is LIVE!", body, urgency="critical")

    # Abstract methods to be implemented by subclasses
    @abstractmethod
    async def on_ready(self):
        """Called when the bot is ready and connected"""
        pass

    @abstractmethod
    async def on_stream_online(
        self, payload: twitchio.StreamOnline, title: str, category: str
    ):
        """Called when stream goes online"""
        pass

    @abstractmethod
    async def on_stream_offline(self, payload: twitchio.StreamOffline):
        """Called when stream goes offline"""
        pass

    @abstractmethod
    async def on_chat_message(self, payload: twitchio.ChatMessage):
        """Called when chat message is received (if chat monitoring enabled)"""
        pass
