# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This project uses **Nix flakes** for reproducible development environments. All Python dependencies (twitchIO, python-telegram-bot) are managed through the flake.

### Essential Commands

```bash
# Enter development shell with all dependencies
nix develop

# Run any stream notifier (inside dev shell)
python stream_notifier_broadcast.py        # Recommended: broadcasts to all chats
python stream_notifier_telegram.py         # Single chat version
python stream_notifier_oauth.py           # OAuth-based with web auth

# Format code (runs automatically on commit via treefmt hook)
nix fmt                                    # Formats Python (black) and Nix (nixfmt)

# Convert Twitch username to user ID
python get_user_id.py <username>
```

## Architecture Overview

This is a **Twitch stream notification system** with multiple implementations, all sharing the same core pattern:

### Core Components

1. **TwitchIO Integration**: Uses `commands.AutoBot` with EventSub conduits for reliable stream monitoring
2. **Notification Backends**: Desktop (`notify-send`) + Telegram messaging  
3. **Event Subscriptions**: `StreamOnlineSubscription`, `StreamOfflineSubscription`, optional `ChatMessageSubscription`

### Implementation Variants

- **`stream_notifier_broadcast.py`** - **Recommended**: Auto-discovers and broadcasts to all Telegram chats the bot is in
- **`stream_notifier_telegram.py`** - Single chat version requiring `TELEGRAM_CHAT_ID`
- **`stream_notifier_oauth.py`** - OAuth-based with web authentication flow for chat monitoring

### Key Architectural Patterns

**EventSub with Conduits**: All implementations use TwitchIO's AutoBot with conduit transport, which:
- Only requires app tokens (no user authentication for basic stream monitoring)
- Maintains 72-hour subscription persistence  
- Auto-reconnects and manages WebSocket connections

**Dual Notification System**: Both desktop notifications (Linux `notify-send`) and Telegram messages are sent simultaneously when streams go live.

**Chat Discovery & Persistence**: The broadcast version uses JSON file storage (`telegram_chats.json`) to remember all chats, with automatic registration via Telegram handlers.

## Environment Configuration

Required environment variables are documented in `.env.example`. The broadcast version only needs:
- Twitch app credentials (`TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`)  
- Target streamer user ID (`TWITCH_TARGET_USER`)
- Telegram bot token (`TELEGRAM_BOT_TOKEN`)

Optional: `TWITCH_BOT_ID` enables Twitch chat monitoring (requires more complex OAuth setup).

## Code Formatting

The repository uses **treefmt** with Black for Python and nixfmt for Nix files. Formatting runs automatically on git commits via pre-commit hooks. The `treefmt.toml` configuration enforces consistent code style across all Python files.

## Telegram Bot Setup

Telegram integration requires bot creation via @BotFather. The broadcast version auto-discovers chats through:
- `/start` command registration
- Auto-registration when messages are sent in group chats
- Persistent storage in `telegram_chats.json`

See `BROADCAST_SETUP.md` and `TELEGRAM_SETUP.md` for detailed setup instructions.