# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This project uses **Nix flakes** for reproducible development environments. All Python dependencies (twitchIO, python-telegram-bot) are managed through the flake.

### Essential Commands

```bash
# Enter development shell with all dependencies
nix develop

# GTG CLI - Unified stream notifier with subcommands (inside dev shell)
python gtg.py broadcast              # Recommended: broadcasts to all Telegram chats
python gtg.py single-chat            # Single chat version
python gtg.py oauth                  # OAuth-based with web auth
python gtg.py get-user-id <username> # Convert Twitch username to user ID

# Alternative execution method
python -m gtg <command>               # Module execution style

# Format code (runs automatically on commit via treefmt hook)
nix fmt                              # Formats Python (black) and Nix (nixfmt)

# Legacy standalone scripts (deprecated, use GTG CLI instead)
python stream_notifier_broadcast.py  # Use: gtg broadcast
python stream_notifier_telegram.py   # Use: gtg single-chat
python stream_notifier_oauth.py      # Use: gtg oauth
python get_user_id.py <username>     # Use: gtg get-user-id
```

## Architecture Overview

This is a **unified Twitch stream notification CLI** (`gtg`) that consolidates multiple notification strategies into a single command-line interface.

### GTG CLI Structure

```
gtg/
├── cli.py                    # Main CLI entry point with Click commands
├── core/                     # Shared core components
│   ├── twitch.py            # BaseTwitchNotifier - common AutoBot patterns
│   ├── notifications.py     # Desktop notification functions
│   └── config.py            # Environment variable handling
├── telegram/                 # Telegram notification strategies
│   ├── base.py              # TelegramNotifier abstract interface
│   ├── single.py            # SingleChatNotifier implementation
│   ├── broadcast.py         # BroadcastNotifier with chat discovery
│   └── chat_manager.py      # Persistent chat storage management
└── commands/                 # CLI subcommand implementations
    ├── broadcast.py         # gtg broadcast - auto-discovers Telegram chats
    ├── single_chat.py       # gtg single-chat - single chat notifications
    ├── oauth.py             # gtg oauth - OAuth web authentication flow
    └── user_id.py           # gtg get-user-id - username to ID conversion
```

### Core Components

1. **TwitchIO Integration**: Uses `commands.AutoBot` with EventSub conduits for reliable stream monitoring
2. **Notification Backends**: Desktop (`notify-send`) + Telegram messaging  
3. **Event Subscriptions**: `StreamOnlineSubscription`, `StreamOfflineSubscription`, optional `ChatMessageSubscription`

### CLI Commands

- **`gtg broadcast`** - **Recommended**: Auto-discovers and broadcasts to all Telegram chats the bot is in
- **`gtg single-chat`** - Single chat version requiring `TELEGRAM_CHAT_ID`
- **`gtg oauth`** - OAuth-based with web authentication flow for chat monitoring
- **`gtg get-user-id <username>`** - Convert Twitch username to user ID

### Key Architectural Patterns

**EventSub with Conduits**: All implementations use TwitchIO's AutoBot with conduit transport, which:
- Only requires app tokens (no user authentication for basic stream monitoring)
- Maintains 72-hour subscription persistence  
- Auto-reconnects and manages WebSocket connections

**Dual Notification System**: Both desktop notifications (Linux `notify-send`) and Telegram messages are sent simultaneously when streams go live.

**Chat Discovery & Persistence**: The broadcast version uses JSON file storage (`telegram_chats.json`) to remember all chats, with automatic registration via Telegram handlers.

## Environment Configuration

Required environment variables are documented in `.env.example`. Each command requires different variables:

**All commands:**
- `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET` - Twitch app credentials

**Stream monitoring commands (broadcast, single-chat, oauth):**
- `TWITCH_TARGET_USER` - Target streamer user ID to monitor
- `TELEGRAM_BOT_TOKEN` - Telegram bot token (except oauth without Telegram)
- `TELEGRAM_CHAT_ID` - Required only for `single-chat` command

**Optional:**
- `TWITCH_BOT_ID` - Enables Twitch chat monitoring (requires OAuth setup)

## Code Formatting

The repository uses **treefmt** with Black for Python and nixfmt for Nix files. Formatting runs automatically on git commits via pre-commit hooks. The `treefmt.toml` configuration enforces consistent code style across all Python files.

## Telegram Bot Setup

Telegram integration requires bot creation via @BotFather. The broadcast version auto-discovers chats through:
- `/start` command registration
- Auto-registration when messages are sent in group chats
- Persistent storage in `telegram_chats.json`

See `BROADCAST_SETUP.md` and `TELEGRAM_SETUP.md` for detailed setup instructions.