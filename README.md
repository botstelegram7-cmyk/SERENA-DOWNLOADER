# SERENA

A Telegram media downloader bot built with **Pyrogram**, **MongoDB**, **FFmpeg**, and an external media API. SERENA can search for music and process supported media links directly inside Telegram, including inline mode and clone-bot management.

The repository includes a Docker image, a Render Web Service health endpoint, Docker Compose for local development, and a safe `.env.example` template.

> **Important:** `API_URL=https://api.arcmusic.fun` is the existing external media API endpoint used by this code. The hostname is intentionally unchanged because it is an API dependency, not the SERENA brand. You must have a valid API key from that API provider or use a compatible API with the same endpoints.

## Features

- YouTube search, tracks, and playlists
- Spotify, SoundCloud, Apple Music, and JioSaavn support
- Instagram, Facebook, Threads, Bluesky, TikTok, Twitter/X, Pinterest, Reddit, and Terabox flows
- Telegram inline mode and group support
- Multi-language catalog: English, Spanish, Burmese, and Russian
- MongoDB-backed users, languages, and clone-bot records
- FFmpeg conversion and media delivery
- Docker and Docker Compose support
- Render-compatible HTTP health server at `/health`
- Configurable update-channel button and download directory

## Repository structure

```text
.
├── bot/
│   ├── assets/       # Profile artwork and static assets
│   ├── core/         # Config, Telegram client, MongoDB, clones, health server
│   ├── dl/           # API client, download and media-delivery flows
│   ├── handlers/     # Telegram message, callback, inline and admin handlers
│   ├── local/        # Translation JSON catalogs
│   └── utils/        # Classifiers, keyboards, caches and helpers
├── Dockerfile
├── docker-compose.yml
├── render.yaml       # Optional Render Blueprint configuration
├── requirements.txt
├── .env.example
└── README.md
```

## Credentials: where to get each value

Never commit `.env`, bot tokens, API hashes, API keys, or database passwords to GitHub. Set them as Render environment variables or keep them only in your local `.env` file.

| Variable | Required | Where it comes from |
|---|---:|---|
| `API_ID` | Yes | Telegram API development tools: [my.telegram.org/auth?to=apps](https://my.telegram.org/auth?to=apps) |
| `API_HASH` | Yes | Created beside `API_ID` in Telegram API development tools: [my.telegram.org/auth?to=apps](https://my.telegram.org/auth?to=apps) |
| `BOT_TOKEN` | Yes | Create/manage the bot through Telegram's official [@BotFather](https://t.me/BotFather) |
| `API_URL` | Yes | Existing media API endpoint: [api.arcmusic.fun](https://api.arcmusic.fun). Keep it unchanged unless you have a compatible replacement. |
| `API_KEY` | Yes | The API requires this query parameter. See its [interactive API docs](https://api.arcmusic.fun/docs); obtain the actual key from the API owner/operator. It is not a Telegram token and is not issued by Render. |
| `MONGO_URI` | Yes | Create a MongoDB database at [MongoDB Atlas](https://www.mongodb.com/atlas/database), then copy its connection string. |
| `OWNER_ID` | Yes | Your numeric Telegram user ID. You can retrieve it through a trusted Telegram user-ID bot such as [@userinfobot](https://t.me/userinfobot). |
| `SUDO_USERS` | Yes | Comma-separated numeric Telegram user IDs allowed to use admin commands. `OWNER_ID` is added automatically. |
| `UPDATES_CHANNEL_URL` | Optional | Your own Telegram updates channel URL, for example `https://t.me/your_channel`. |
| `APP_NAME` | Optional | Keep this as `SERENA` for the current branding. |
| `HOST` / `PORT` | Managed | Local defaults are `0.0.0.0` and `10000`. Render injects `PORT` automatically. |

### Telegram setup

1. Open [@BotFather](https://t.me/BotFather) and run `/newbot`.
2. Copy the generated value into `BOT_TOKEN`.
3. Open [Telegram API development tools](https://my.telegram.org/auth?to=apps), sign in, create an application, and copy `API_ID` and `API_HASH`.
4. Send a message to your bot once it is online and confirm your numeric Telegram ID for `OWNER_ID`.
5. If clone-bot features are enabled, follow the bot's `/start` instructions and complete the manual inline-mode steps in @BotFather.

### MongoDB Atlas setup

1. Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/atlas/database).
2. Create a database user and password.
3. Add the required network access rule. For a quick test, Atlas allows `0.0.0.0/0`; for production, restrict access where possible.
4. Copy the `mongodb+srv://...` connection string into `MONGO_URI`.
5. Use a database name such as `serena` in `MONGO_DB` or in the connection string.

## Environment setup

Create a local environment file from the template:

```bash
cp .env.example .env
```

Fill in every required placeholder. `.env` is ignored by Git; `.env.example` contains placeholders only.

For local Docker Compose, keep:

```env
MONGO_URI=mongodb://mongo:27017/serena
MONGO_DB=serena
```

For Render, replace `MONGO_URI` with the MongoDB Atlas connection string. Do not use `mongodb://localhost:27017` on Render; that points to the bot container itself, not Atlas.

## Run locally with Python

Python 3.12 is recommended.

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
python -m bot
```

The local health endpoint is available at <http://localhost:10000/health> when `PORT=10000`.

## Run with Docker Compose

Docker Desktop or Docker Engine with Compose is required.

```bash
cp .env.example .env
# Keep MONGO_URI=mongodb://mongo:27017/serena for the bundled MongoDB service.
docker compose up --build
```

Check the health endpoint:

```bash
curl http://localhost:10000/health
```

Stop the services:

```bash
docker compose down
```

MongoDB data is stored in the named `mongo-data` volume. Downloaded media is stored in the local `downloads/` directory and is cleaned up by the bot after delivery where applicable.

## Deploy on Render as a Web Service

Render Web Services expect an HTTP listener. SERENA starts a lightweight `aiohttp` health server and binds to `0.0.0.0:$PORT`, while the Telegram bot continues running in the same process.

### Option A: Render Blueprint

1. Push this repository to GitHub.
2. Open the [Render Dashboard](https://dashboard.render.com/).
3. Choose **New + → Blueprint** and select this repository.
4. Render will read `render.yaml` and create the Docker-based web service.
5. Open the service's **Environment** page and enter all `sync: false` values.
6. Deploy and check `https://YOUR-SERVICE.onrender.com/health`.

### Option B: Create the service manually

1. Open [Render New Web Service](https://dashboard.render.com/select-repo?type=web).
2. Connect `botstelegram7-cmyk/SERENA-DOWNLOADER`.
3. Select branch `main`.
4. Choose **Docker** as the runtime. The repository `Dockerfile` is used automatically.
5. Set the health check path to `/health`.
6. Add the environment variables from the table above, especially `API_ID`, `API_HASH`, `BOT_TOKEN`, `API_KEY`, `MONGO_URI`, `OWNER_ID`, and `SUDO_USERS`.
7. Start the deployment. Do not override the Docker command; the image already runs `python -m bot`.
8. Verify the service at:

   ```text
   https://YOUR-SERVICE-NAME.onrender.com/health
   ```

Render supplies `PORT` at runtime. The application does not hard-code a public port and listens on `0.0.0.0`, so it is compatible with Render's web-service proxy.

### Render notes

- Use MongoDB Atlas for `MONGO_URI`; Render's Docker container does not include MongoDB.
- The local filesystem of a Render service is ephemeral. SERENA treats downloaded media as temporary and removes it after sending where possible.
- A free Render instance can sleep or restart. For continuous Telegram polling, use a plan/configuration that keeps the service running; the `/health` endpoint only satisfies the web-service HTTP requirement.
- If deployment fails, open **Logs** and first check missing environment variables, MongoDB network access, the external `API_KEY`, and Telegram credentials.

## Updating the bot

```bash
git pull origin main
git add .
git commit -m "Describe your change"
git push origin main
```

Render can automatically redeploy after a push if auto-deploy is enabled.

## Security and legal notes

- Treat `BOT_TOKEN`, `API_HASH`, `API_KEY`, `MONGO_URI`, and clone-bot tokens as secrets.
- If a secret is ever pasted into a chat or committed to Git, revoke/rotate it immediately and remove it from Git history where necessary.
- Use the downloader only with content and services you are authorised to access. Respect each platform's terms, copyright rules, and Telegram policies.
- The repository retains the MIT license in `LICENSE`. Review upstream attribution and licensing before redistributing a modified build.
