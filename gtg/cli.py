"""Main CLI interface for GTG stream notifier"""

import asyncio
import logging
import sys

import click
import twitchio

from .core.config import load_config, validate_required
from .commands.single_chat import run_single_chat
from .commands.broadcast import run_broadcast
from .commands.oauth import run_oauth


@click.group()
@click.version_option()
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def cli(verbose):
    """GTG - Stream notification system for Twitch"""
    level = logging.DEBUG if verbose else logging.ERROR
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    # Set third-party library logging to ERROR unless verbose
    if not verbose:
        logging.getLogger("twitchio").setLevel(logging.ERROR)
        logging.getLogger("twitchio.web").setLevel(logging.ERROR)
        logging.getLogger("aiohttp").setLevel(logging.ERROR)
        logging.getLogger("websockets").setLevel(logging.ERROR)


@cli.command()
def broadcast():
    """Run stream notifier with Telegram broadcast to all chats

    Automatically discovers and broadcasts to all chats the bot is added to.
    Requires: TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_TARGET_USER, TELEGRAM_BOT_TOKEN
    Optional: TWITCH_BOT_ID (enables chat monitoring)
    """
    required = [
        "TWITCH_CLIENT_ID",
        "TWITCH_CLIENT_SECRET",
        "TWITCH_TARGET_USER",
        "TELEGRAM_BOT_TOKEN",
    ]
    if not validate_required(required):
        sys.exit(1)

    asyncio.run(run_broadcast())


@cli.command()
def single_chat():
    """Run stream notifier for a single Telegram chat

    Sends notifications to one specific chat.
    Requires: TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_TARGET_USER,
              TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    Optional: TWITCH_BOT_ID (enables chat monitoring)
    """
    required = [
        "TWITCH_CLIENT_ID",
        "TWITCH_CLIENT_SECRET",
        "TWITCH_TARGET_USER",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]
    if not validate_required(required):
        sys.exit(1)

    asyncio.run(run_single_chat())


@cli.command()
def oauth():
    """Run stream notifier with OAuth web authentication

    Uses OAuth flow with web interface for authentication.
    Requires: TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_BOT_ID, TELEGRAM_BOT_TOKEN
    Optional: TELEGRAM_CHAT_ID
    """
    required = [
        "TWITCH_CLIENT_ID",
        "TWITCH_CLIENT_SECRET",
        "TWITCH_BOT_ID",
        "TELEGRAM_BOT_TOKEN",
    ]
    if not validate_required(required):
        sys.exit(1)

    asyncio.run(run_oauth())


@cli.command("get-user-id")
@click.argument("username")
def get_user_id(username: str):
    """Convert Twitch username to user ID

    USERNAME: The Twitch username to look up

    Requires: TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET
    """
    required = ["TWITCH_CLIENT_ID", "TWITCH_CLIENT_SECRET"]
    if not validate_required(required):
        sys.exit(1)

    config = load_config()
    asyncio.run(
        _get_user_id_async(
            username, config["TWITCH_CLIENT_ID"], config["TWITCH_CLIENT_SECRET"]
        )
    )


async def _get_user_id_async(username: str, client_id: str, client_secret: str):
    """Async implementation of get_user_id command"""
    client = twitchio.Client(client_id=client_id, client_secret=client_secret)
    async with client:
        await client.login()
        users = await client.fetch_users(logins=[username])
        if users:
            click.echo(f"User ID for {username}: {users[0].id}")
        else:
            click.echo(f"User not found: {username}")
            sys.exit(1)
