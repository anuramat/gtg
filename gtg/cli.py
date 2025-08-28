"""Main CLI interface for GTG stream notifier"""

import asyncio
import logging
import sys

# Configure logging early to suppress import warnings
logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")
logging.getLogger("twitchio").setLevel(logging.ERROR)
logging.getLogger("twitchio.web").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("websockets").setLevel(logging.ERROR)

import click
import twitchio

from .commands.broadcast import run_broadcast
from .core.config import load_config, validate_required


@click.group()
@click.version_option()
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def cli(verbose):
    """GTG - Stream notification system for Twitch"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("twitchio").setLevel(logging.DEBUG)
        logging.getLogger("twitchio.web").setLevel(logging.DEBUG)
        logging.getLogger("aiohttp").setLevel(logging.DEBUG)
        logging.getLogger("websockets").setLevel(logging.DEBUG)


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
