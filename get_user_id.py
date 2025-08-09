#!/usr/bin/env python3

"""Helper script to convert Twitch username to user ID"""

import asyncio
import os
import sys

import twitchio


async def get_user_id(username: str, client_id: str, client_secret: str) -> str | None:
    """Convert username to user ID using Twitch API"""
    client = twitchio.Client(client_id=client_id, client_secret=client_secret)
    async with client:
        await client.login()  # Initialize the client and app token
        users = await client.fetch_users(logins=[username])
        if users:
            return users[0].id
        return None


async def main():
    if len(sys.argv) < 2:
        print("Usage: python get_user_id.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")

    if client_id is None or client_secret is None:
        print(
            "Error: Set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET environment variables"
        )
        sys.exit(1)

    user_id = await get_user_id(username, client_id, client_secret)
    if user_id:
        print(f"User ID for {username}: {user_id}")
    else:
        print(f"User not found: {username}")


if __name__ == "__main__":
    asyncio.run(main())
