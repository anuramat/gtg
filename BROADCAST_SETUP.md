# Telegram Broadcast Setup Guide

The broadcast version automatically sends stream notifications to **all groups/chats** the bot is added to.

## Key Features

- **Auto-discovery**: Bot automatically learns about new chats
- **Persistent storage**: Remembers chats in `telegram_chats.json`
- **Automatic cleanup**: Removes invalid/blocked chats
- **Commands**: `/start` and `/status` for management

## Setup Instructions

### 1. Create and Configure Bot
Same as regular setup - create bot via @BotFather

### 2. Add Bot to Groups
- Add your bot to any Telegram groups you want notifications in
- The bot doesn't need admin privileges, just ability to send messages

### 3. Register Chats
**Method 1: Send `/start` command**
```
/start
```
Bot replies: ✅ Stream notifications enabled!

**Method 2: Auto-registration**
- Just send any message in a group chat
- Bot automatically registers group chats (not private chats)

### 4. Check Status
```
/status
```
Shows:
- Currently monitored streamer
- Number of registered chats  
- Current chat ID

## Environment Variables

Only need the bot token now - no specific chat ID required:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
# No TELEGRAM_CHAT_ID needed for broadcast version!
```

## Running

```bash
nix develop -c python stream_notifier_broadcast.py
```

## File Storage

- **`telegram_chats.json`** - Stores all registered chat IDs
- Automatically created and updated
- Contains chat IDs and last update timestamp

## Commands Available in Telegram

| Command | Description |
|---------|-------------|
| `/start` | Register this chat for notifications |
| `/status` | Show bot status and chat info |

## How It Works

1. **First run**: No chats registered, creates empty `telegram_chats.json`
2. **Add to groups**: Bot detects new groups when messages are sent
3. **Registration**: Groups auto-register or use `/start` command  
4. **Broadcasting**: When stream goes live, sends to all registered chats
5. **Cleanup**: Removes chats where bot was blocked/kicked

## Troubleshooting

- **No notifications**: Send `/start` in your groups
- **Missing groups**: Send any message to trigger auto-registration
- **Bot removed**: It will auto-remove invalid chats from storage
- **File corruption**: Delete `telegram_chats.json` to start fresh

## Migration from Single-Chat Version

The broadcast version doesn't need `TELEGRAM_CHAT_ID` - it discovers chats automatically. Just:

1. Remove `TELEGRAM_CHAT_ID` from your environment
2. Use `stream_notifier_broadcast.py` instead  
3. Send `/start` in existing groups to re-register them