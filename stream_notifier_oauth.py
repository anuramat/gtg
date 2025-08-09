#!/usr/bin/env python3
"""
Proper TwitchIO stream notifier following the official documentation pattern.
Requires OAuth authentication via web browser for chat monitoring.
"""
import asyncio
import datetime
import json
import os
import subprocess

import twitchio
from twitchio import eventsub
from twitchio.ext import commands


class StreamNotifier(commands.AutoBot):
    def __init__(self, client_id: str, client_secret: str, bot_id: str):
        # Start with empty subscriptions - they'll be added when users authenticate
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            prefix="!",
            subscriptions=[],  # Dynamic subscriptions
        )

    async def event_ready(self):
        """Called when bot is ready"""
        print("Stream notifier is ready!")
        print("To monitor a channel:")
        print("1. Visit http://localhost:4343/oauth?scopes=channel:bot")
        print("2. Log in as the streamer you want to monitor")
        print("3. The bot will automatically subscribe to their events")

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
        print(
            f"[{timestamp}] [LIVE] {payload.broadcaster.display_name} started streaming!"
        )

        # Send desktop notification
        try:
            subprocess.run(
                [
                    "notify-send",
                    "-u",
                    "critical",
                    "-i",
                    "video-display",
                    f"{payload.broadcaster.display_name} is LIVE!",
                    "Stream has started",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to send notification: {e}")

    async def event_stream_offline(self, payload: twitchio.StreamOffline):
        """Handle stream offline event"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(
            f"[{timestamp}] [OFFLINE] {payload.broadcaster.display_name} went offline"
        )

    async def event_message(self, payload: twitchio.ChatMessage):
        """Handle chat messages"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # Determine user type
        if payload.chatter.moderator:
            prefix = "[MOD]"
        elif payload.chatter.subscriber:
            prefix = "[SUB]"
        else:
            prefix = "[CHAT]"

        print(f"[{timestamp}] {prefix} {payload.chatter.display_name}: {payload.text}")


async def main():
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    bot_id = os.getenv("TWITCH_BOT_ID")

    if not all([client_id, client_secret, bot_id]):
        print("Error: Missing required environment variables")
        print("Required: TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_BOT_ID")
        print()
        print("Setup instructions:")
        print("1. Create a bot Twitch account")
        print("2. Get the bot's user ID")
        print("3. Create a Twitch app at https://dev.twitch.tv/console/apps")
        print("4. Set redirect URI to: http://localhost:4343/oauth/callback")
        return

    print(f"Starting stream notifier with bot ID: {bot_id}")

    try:
        async with StreamNotifier(client_id, client_secret, bot_id) as bot:
            await bot.start()
    except KeyboardInterrupt:
        print("\nShutting down stream notifier...")


if __name__ == "__main__":
    asyncio.run(main())
