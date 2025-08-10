# Telegram Bot Setup Guide

## 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat and send `/newbot`
3. Follow the prompts to name your bot
4. Save the **Bot Token** (looks like: `123456789:ABCdefGhIJKlmnoPQRstu-vwxYZ`)

## 2. Add Bot to Your Group

1. Create a Telegram group or use existing one
2. Add your bot to the group as an admin
3. Give it permission to send messages

## 3. Get Group Chat ID

### Method 1: Using @userinfobot
1. Add **@userinfobot** to your group
2. The bot will automatically show the group chat ID
3. Remove @userinfobot after getting the ID

### Method 2: Using @get_id_bot
1. Add **@get_id_bot** to your group  
2. Send any message to the group
3. The bot will reply with chat information

### Method 3: Manual API call
```bash
# Replace YOUR_BOT_TOKEN with your actual token
curl https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

## 4. Configure Environment Variables

Add to your `.envrc`:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_group_chat_id_here"
```

Group chat IDs are usually negative numbers like: `-1001234567890`

## 5. Test the Bot

```bash
nix develop -c python stream_notifier_telegram.py
```

You should see:
- `[TELEGRAM] Connected as: YourBotName (@yourbotusername)`
- Bot ready and waiting for stream events

## Troubleshooting

- **Bot can't send messages**: Make sure bot is admin in group
- **Wrong chat ID**: Use @userinfobot to verify the correct ID  
- **Invalid token**: Double-check token from @BotFather
- **403 Forbidden**: Bot might be blocked or not added to group