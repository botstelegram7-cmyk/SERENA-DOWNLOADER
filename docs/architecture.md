# SERENA Architecture

SERENA is an enterprise-grade, modular Telegram media downloader engine designed for high throughput, seamless clone scaling, and serverless/PaaS deployment.

---

## Directory & Package Structure

```text
.
├── bot.py                # Backward compatibility entrypoint (python -m bot)
├── Dockerfile            # Multi-stage optimized container definition
├── docker-compose.yml    # Local development with bundled MongoDB
├── render.yaml           # Infrastructure-as-code Blueprint for Render
├── requirements.txt      # Pinned production Python dependencies
├── .env.example          # Environment variables template
├── docs/                 # Detailed guides (Render, BotFather, Architecture)
│   ├── architecture.md
│   ├── botfather.md
│   └── render.md
└── serena/               # Core application package
    ├── assets/           # Brand assets (serena_logo.png)
    ├── core/             # Framework, database, clones, configuration & HTTP
    │   ├── client.py     # Main Pyrogram MTProto client instance
    │   ├── clones.py     # Clone manager for multi-bot lifecycle
    │   ├── config.py     # Environment loader and validator
    │   ├── dirs.py       # Temporary download directory setup
    │   ├── health.py     # aiohttp health & Telegram webhook server
    │   └── mongo.py      # Async MongoDB layer with connection pooling
    ├── dl/               # Media extraction, transcoding & delivery
    │   ├── actions.py    # Download dispatcher and chat messenger
    │   ├── api_client.py # Multi-key Arc API client with failover
    │   ├── downloader.py # Streaming chunk downloader with progress
    │   ├── ffmpeg.py     # FFmpeg audio/video probe & metadata tagger
    │   └── terabox_flow.py # Terabox resolution and multi-file sender
    ├── handlers/         # Telegram event handlers
    │   ├── admin.py      # /stats, /broadcast, maintenance
    │   ├── callback.py   # Inline button callback queries
    │   ├── clones.py     # /mybot, clone toggle/delete, managed_bot update
    │   ├── inline.py     # Inline mode queries & result delivery
    │   ├── lang.py       # Multi-language selection (/lang)
    │   ├── search.py     # Search triggers & platform link interceptors
    │   └── start.py      # /start, deep link clone flow, /privacy
    ├── local/            # Internationalization (i18n) catalogs
    │   ├── en.json       # English (default)
    │   ├── es.json       # Spanish
    │   ├── my.json       # Burmese
    │   └── ru.json       # Russian
    └── utils/            # Shared utilities and helper functions
        ├── buttons.py    # Inline keyboard builders & deep link generator
        ├── classifier.py # Link & media regex classifier
        ├── helper.py     # Registries, uptime, caches, mojibake fixer
        └── search_flow.py # Unified search pipeline
```

---

## Key Subsystems

### 1. Dual HTTP Webhook + MTProto Engine

SERENA simultaneously runs an `aiohttp` web server and a Pyrogram MTProto client in a single unified event loop:
- **aiohttp Web Server:** Listens on `0.0.0.0:$PORT` to serve `/health`, `/healthz`, `/wake`, and `/telegram/webhook`.
- **Telegram Bot API Webhook:** Automatically registered with Telegram on startup using `effective_webhook_url`. Incoming webhook POSTs wake up sleeping Render containers instantly.
- **MTProto Pyrogram Client:** Provides raw Telegram speed, large file uploads up to 2 GB, inline querying, and managed bot token export.

### 2. Backward Compatibility Layer (`bot.py`)

To ensure backward compatibility with existing commands (`python -m bot`, Docker `CMD ["python", "-m", "bot"]`, and custom deployment scripts), root `bot.py` forwards execution to `serena.__main__.main()` and exports `serena` symbols.

### 3. Clone Bot Manager (`serena/core/clones.py`)

- Cloned bots are managed using Telegram's official **Managed Bot** framework.
- Deep links format: `https://t.me/newbot/<MANAGER_USERNAME>/<SUGGESTED_USERNAME>?name=<SUGGESTED_NAME>`.
- When a user creates a bot through BotFather, Telegram emits a `ManagedBotUpdated` event.
- SERENA exports the bot token via `ExportBotToken`, sets branding (profile picture, description), and spins up a dedicated `Client` in memory.
- Clone records persist in MongoDB and auto-relaunch across server restarts.

### 4. Resilient Arc API Client (`serena/dl/api_client.py`)

- Supports single `API_KEY` or multiple fallback `API_KEYS` (`key1,key2,key3`).
- Detects quota exhaustion (`429`), authorization failures (`401`/`403`), and network timeouts.
- Automatically rotates to backup keys on failover without interrupting user downloads.
- Retries transient network glitches with exponential backoff.

### 5. Media Pipeline & Cleanup

1. User sends a query or link (YouTube, Spotify, Apple Music, JioSaavn, SoundCloud, Instagram, TikTok, Terabox, etc.).
2. The URL classifier detects platform and triggers appropriate API or extraction workflow.
3. Audio/video chunks stream into `downloads/` temporary storage.
4. FFmpeg applies ID3 tags, album art, duration metadata, and audio encoding.
5. Media is delivered directly to Telegram.
6. Temporary media files are immediately deleted from disk to keep storage footprint minimal.
