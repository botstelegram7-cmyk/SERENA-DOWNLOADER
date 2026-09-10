# BotFather Configuration Guide

This guide walks you through configuring your Telegram bot in [@BotFather](https://t.me/BotFather) for SERENA, enabling **Bot Management Mode**, setting up **Inline Mode**, and resetting old reply menus.

---

## 1. Creating the Manager Bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram.
2. Send `/newbot` and follow the prompts to choose a name and username.
3. Save the **Bot Token** (format `123456789:ABC...`) to your environment as `BOT_TOKEN`.

---

## 2. Enabling Bot Management Mode (Crucial for Clone Bots)

To allow users to clone SERENA into their own bots via deep links, you **must enable Bot Management Mode**:

1. Send `/mybots` in [@BotFather](https://t.me/BotFather).
2. Select your SERENA bot from the list.
3. Click **Bot Settings** (this opens the BotFather Mini App or inline menu).
4. Tap **Bot Management Mode**.
5. Toggle it to **Enabled**.

> **Note:** If Bot Management Mode is disabled in BotFather, SERENA will automatically detect this via `client.me.can_manage_bots` and safely hide the clone button in `/start` to prevent confusing errors for users.

---

## 3. Configuring Inline Mode & Feedback

SERENA supports inline queries (e.g. `@YourBot song name` in any chat). Configure these settings:

1. Send `/setinline` to [@BotFather](https://t.me/BotFather).
2. Select your bot.
3. Enter a placeholder text:
   ```text
   Search songs or paste a link...
   ```
4. Send `/setinlinefeedback` to [@BotFather](https://t.me/BotFather).
5. Select your bot and set feedback percentage to **100%** (enables accurate delivery tracking).

---

## 4. Resetting Reply Keyboards / Menu Button (`/empty`)

If you or your users previously used the old `request_managed_bot` reply keyboard, Telegram clients may still show the old custom keyboard.

### Steps to Clear Old Keyboard in Telegram:
1. In private chat with your bot, send `/empty` or `/start`.
2. The bot responds with the new inline keyboard, replacing any legacy buttons.
3. In [@BotFather](https://t.me/BotFather), you can also verify menu button settings:
   - Send `/setmenubutton` → Choose bot → Choose default.

---

## 5. How the Clone Flow Works

SERENA uses Telegram's official deep link URL for bot creation:

```text
https://t.me/newbot/<MANAGER_USERNAME>/<SUGGESTED_USERNAME>?name=<SUGGESTED_NAME>
```

When a user taps **🤖 Clone this bot**:
1. Telegram opens BotFather with the manager bot pre-selected and a suggested name/username.
2. The user confirms creation in BotFather.
3. Telegram emits a `ManagedBotUpdated` event to SERENA.
4. SERENA exports the bot token securely, sets official SERENA branding & descriptions, and spins up the clone bot in memory.
5. The owner receives a confirmation message with instructions to manage their bot via `/mybot`.
