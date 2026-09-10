# Deploying SERENA on Render (Free Web Service)

SERENA is optimized to run as a **Free Web Service** on [Render](https://render.com) using Telegram Bot API webhooks for serverless-style auto-wake functionality.

---

## How Render Free Wake Works

Render automatically puts free web services to sleep after 15 minutes of inactivity to save compute resources.

### Previous Long-Polling vs. Webhook Architecture

| Mode | Behavior on Render Free | Wake Capability | External Monitor Needed? |
|---|---|---|---|
| **Old (Long Polling)** | PyroTGFork listens over persistent MTProto socket. When Render sleeps the container, socket closes. | ❌ Telegram messages cannot wake a sleeping service. | **Yes** (required third-party pings like UptimeRobot) |
| **New (Webhook Mode)** | Telegram Bot API is registered with webhook URL `https://YOUR-SERVICE.onrender.com/telegram/webhook`. | ✅ Incoming Telegram messages trigger HTTP POST to Render, waking the container automatically. | **No** (wake-on-request is self-contained) |

```text
User sends Telegram message
        │
        ▼
Telegram Bot API
        │
        ▼ (HTTP POST /telegram/webhook)
Render Web Service Router ───► [Container Asleep]
        │                              │
        │ (Wakes container up)          │ (Cold start ~45-60s)
        ▼                              ▼
SERENA Health & Webhook Server ◄───────┘
        │
        ▼
Pyrogram MTProto Engine processes media download & sends to user
```

> **Note on Cold Starts:** When Render Free wakes from sleep, startup takes approximately 45–60 seconds. Once awake, requests respond instantly.

---

## Webhook & Health Endpoints

SERENA runs an integrated `aiohttp` server listening on `0.0.0.0:$PORT`:

| Endpoint | Method | Purpose |
|---|---|---|
| `/telegram/webhook` | `POST` | Telegram Bot API webhook receiver. Wakes Render and acknowledges updates. |
| `/health` | `GET` | Render deployment health check probe. |
| `/healthz` | `GET` | Kubernetes / container standard health check. |
| `/wake` | `GET` | Direct endpoint to manually ping or wake the service. |
| `/` | `GET` | Status overview JSON with service name, version, and active routes. |

### Webhook Security

You can configure `WEBHOOK_SECRET` in your environment. When set:
- SERENA includes `secret_token` when registering with Telegram Bot API (`setWebhook`).
- Incoming requests to `/telegram/webhook` are verified against the `X-Telegram-Bot-Api-Secret-Token` header.
- Requests with mismatched or missing secret tokens return `403 Forbidden`.

---

## Step-by-Step Render Deployment

### 1. Push Code to GitHub

Ensure your repository is pushed to your GitHub account.

### 2. Create Web Service on Render

1. Log into [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** → **Web Service**.
3. Select your repository (`SERENA-DOWNLOADER`).
4. Set the following basic parameters:
   - **Name:** `serena` (or custom name)
   - **Runtime:** `Docker`
   - **Instance Type:** `Free`
   - **Health Check Path:** `/health`

### 3. Configure Environment Variables

Under the **Environment** section, add the required variables:

| Variable | Required | Description | Example |
|---|---:|---|---|
| `API_ID` | Yes | Telegram API ID from [my.telegram.org](https://my.telegram.org) | `1234567` |
| `API_HASH` | Yes | Telegram API Hash from [my.telegram.org](https://my.telegram.org) | `0123456789abcdef` |
| `BOT_TOKEN` | Yes | Main bot token from [@BotFather](https://t.me/BotFather) | `123456:ABC-DEF...` |
| `API_URL` | Yes | Media API endpoint | `https://api.arcmusic.fun` |
| `API_KEYS` | Yes | Arc API keys (comma-separated fallback keys) | `key_one,key_two` |
| `MONGO_URI` | Yes | MongoDB Atlas connection string | `mongodb+srv://user:pass@cluster.mongodb.net/serena` |
| `MONGO_DB` | No | Database name (default: `serena`) | `serena` |
| `OWNER_ID` | Yes | Numeric Telegram ID of owner | `123456789` |
| `SUDO_USERS` | Yes | Sudo user IDs (comma-separated) | `123456789,987654321` |
| `UPDATES_CHANNEL_URL` | No | Updates channel link | `https://t.me/serenaunzipbot` |
| `WEBHOOK_PATH` | No | Webhook route (default: `/telegram/webhook`) | `/telegram/webhook` |
| `WEBHOOK_SECRET` | No | Secret token for webhook verification | `random_alphanumeric_secret` |

> Render automatically injects `PORT` and `RENDER_EXTERNAL_URL` (e.g. `https://your-service.onrender.com`). SERENA uses `RENDER_EXTERNAL_URL` to automatically register the webhook with Telegram.

### 4. Deploy and Verify

1. Click **Create Web Service**.
2. Watch the deployment logs. You should see:
   ```text
   Connected to MongoDB
   Health server listening on 0.0.0.0:10000
   Registering Telegram Bot API webhook at https://your-service.onrender.com/telegram/webhook...
   Telegram Bot API webhook successfully set to: https://your-service.onrender.com/telegram/webhook
   All modules loaded. Bot is up and running.
   ```
3. Test your service endpoint in your browser:
   `https://YOUR-SERVICE.onrender.com/health` → `{"status": "ok", "service": "SERENA", ...}`
