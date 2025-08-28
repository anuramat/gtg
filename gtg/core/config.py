"""Configuration management for GTG"""

import os
import sys


def load_config() -> dict[str, str | None]:
    """Load all GTG environment variables into a config dict"""
    return {
        "TWITCH_CLIENT_ID": os.getenv("TWITCH_CLIENT_ID"),
        "TWITCH_CLIENT_SECRET": os.getenv("TWITCH_CLIENT_SECRET"),
        "TWITCH_TARGET_USER": os.getenv("TWITCH_TARGET_USER"),
        "TWITCH_BOT_ID": os.getenv("TWITCH_BOT_ID"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
    }


def validate_required(keys: list[str]) -> bool:
    """Validate required environment variables exist and print helpful errors"""
    config = load_config()
    missing = [k for k in keys if not config[k]]

    if missing:
        print("Error: Missing required environment variables:")
        for key in missing:
            print(f"  {key}")

        print("\nSetup instructions:")
        if "TWITCH_CLIENT_ID" in missing or "TWITCH_CLIENT_SECRET" in missing:
            print("1. Create a Twitch app at https://dev.twitch.tv/console/apps")
            print("2. Set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET")

        if "TWITCH_TARGET_USER" in missing:
            print(
                "3. Set TWITCH_TARGET_USER (use get-user-id command to convert username)"
            )

        if "TELEGRAM_BOT_TOKEN" in missing:
            print("4. Create a Telegram bot via @BotFather")
            print("5. Set TELEGRAM_BOT_TOKEN")

        print("\nOptional variables:")
        print("  TWITCH_BOT_ID - enables chat monitoring")

        return False
    return True
