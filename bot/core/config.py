# Licensed under the MIT License.

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _read_int(name: str, default: int = 0) -> int:
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


def _read_id_set(name: str) -> set[int]:
    values: set[int] = set()
    raw = os.getenv(name, "")
    for item in raw.replace(" ", "").split(","):
        if not item:
            continue
        try:
            values.add(int(item))
        except ValueError as exc:
            raise RuntimeError(f"{name} must contain comma-separated numeric Telegram user IDs") from exc
    return values


def _split_keys(raw: str) -> list[str]:
    values: list[str] = []
    for item in raw.replace("\r", "\n").replace("\n", ",").split(","):
        key = item.strip()
        if key and key not in values:
            values.append(key)
    return values


def _read_api_keys() -> tuple[str, ...]:
    """Read the preferred API_KEYS list with API_KEY compatibility.

    API_KEYS is intentionally preferred so a stale legacy API_KEY value cannot
    accidentally become the first key when a user switches to key rotation.
    API_KEY_1, API_KEY_2, ... are also accepted for dashboard-friendly setups.
    """
    configured = _split_keys(os.getenv("API_KEYS", ""))
    for index in range(1, 21):
        configured.extend(_split_keys(os.getenv(f"API_KEY_{index}", "")))

    if configured:
        return tuple(dict.fromkeys(configured))

    return tuple(_split_keys(os.getenv("API_KEY", "")))


class Config:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "SERENA").strip() or "SERENA"

        self.api_id = _read_int("API_ID")
        self.api_hash = os.getenv("API_HASH", "").strip()
        self.bot_token = os.getenv("BOT_TOKEN", "").strip()
        self.bot_id = int(self.bot_token.split(":", 1)[0]) if ":" in self.bot_token else 0

        self.api_url = os.getenv("API_URL", "https://api.arcmusic.fun").strip().rstrip("/")
        self.api_keys = _read_api_keys()
        # Backwards-compatible first key for code that still reads API_KEY.
        self.api_key = self.api_keys[0] if self.api_keys else ""

        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/serena").strip()
        self.mongo_db = os.getenv("MONGO_DB", "serena").strip() or "serena"

        self.owner_id = _read_int("OWNER_ID")
        self.sudo_users = _read_id_set("SUDO_USERS")
        self.sudo_users.add(self.owner_id)

        self.host = os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"
        self.port = _read_int("PORT", 10000)
        self.download_dir = os.getenv("DOWNLOAD_DIR", "downloads").strip() or "downloads"
        self.updates_channel_url = os.getenv(
            "UPDATES_CHANNEL_URL", "https://t.me/serenaunzipbot"
        ).strip()

    def validate(self) -> None:
        missing: list[str] = []
        if self.api_id <= 0:
            missing.append("API_ID")
        if not self.api_hash:
            missing.append("API_HASH")
        if not self.bot_token or ":" not in self.bot_token:
            missing.append("BOT_TOKEN")
        if not self.api_url:
            missing.append("API_URL")
        if not self.api_keys:
            missing.append("API_KEY or API_KEYS")
        if not self.mongo_uri:
            missing.append("MONGO_URI")
        if self.owner_id <= 0:
            missing.append("OWNER_ID")
        if self.port <= 0 or self.port > 65535:
            missing.append("PORT")

        if missing:
            names = ", ".join(dict.fromkeys(missing))
            raise RuntimeError(f"Missing or invalid environment variables: {names}")


config = Config()
