# Licensed under the MIT License.

from __future__ import annotations

import aiohttp
from aiohttp import web

from .. import LOGGER, __bot_name__, __maintainer__, __version__
from .config import config


class HealthServer:
    def __init__(self) -> None:
        self._runner: web.AppRunner | None = None

    async def start(self) -> None:
        if self._runner is not None:
            return

        application = web.Application()
        application.router.add_get("/", self._root)
        application.router.add_get("/health", self._health)
        application.router.add_get("/healthz", self._health)
        application.router.add_get("/wake", self._wake)
        application.router.add_post(config.webhook_path, self._telegram_webhook)

        self._runner = web.AppRunner(application, access_log=None)
        await self._runner.setup()
        site = web.TCPSite(self._runner, host=config.host, port=config.port)
        await site.start()
        LOGGER.info("Health server listening on %s:%s", config.host, config.port)

        await self.register_webhook()

    async def stop(self) -> None:
        if self._runner is None:
            return
        await self._runner.cleanup()
        self._runner = None
        LOGGER.info("Health server stopped.")

    @staticmethod
    async def _root(_request: web.Request) -> web.Response:
        return web.json_response(
            {
                "service": __bot_name__,
                "status": "ok",
                "version": __version__,
                "maintainer": __maintainer__,
                "health": "/health",
                "wake": "/wake",
                "webhook": config.webhook_path,
            }
        )

    @staticmethod
    async def _health(_request: web.Request) -> web.Response:
        return web.json_response(
            {
                "status": "ok",
                "service": __bot_name__,
                "version": __version__,
                "maintainer": __maintainer__,
            }
        )

    @staticmethod
    async def _wake(_request: web.Request) -> web.Response:
        return web.json_response(
            {
                "status": "ok",
                "service": __bot_name__,
                "message": "Bot is awake",
                "version": __version__,
            }
        )

    @staticmethod
    async def _telegram_webhook(request: web.Request) -> web.Response:
        if config.webhook_secret:
            token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if token != config.webhook_secret:
                LOGGER.warning("Telegram webhook secret mismatch from %s", request.remote)
                return web.Response(status=403, text="Forbidden")

        try:
            update = await request.json()
            LOGGER.debug("Received Telegram webhook update ID: %s", update.get("update_id"))
        except Exception:
            pass

        return web.json_response({"ok": True})

    @staticmethod
    async def register_webhook() -> bool:
        webhook_url = config.effective_webhook_url
        if not webhook_url:
            LOGGER.info("No external webhook URL configured. Running without Bot API setWebhook registration.")
            return False

        LOGGER.info("Registering Telegram Bot API webhook at %s...", webhook_url)
        endpoint = f"https://api.telegram.org/bot{config.bot_token}/setWebhook"
        payload: dict[str, object] = {
            "url": webhook_url,
            "drop_pending_updates": False,
            "allowed_updates": [
                "message",
                "edited_message",
                "callback_query",
                "inline_query",
                "chosen_inline_result",
                "managed_bot",
            ],
        }
        if config.webhook_secret:
            payload["secret_token"] = config.webhook_secret

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    data = await resp.json()
                    if data.get("ok"):
                        LOGGER.info("Telegram Bot API webhook successfully set to: %s", webhook_url)
                        return True
                    LOGGER.warning("Telegram Bot API setWebhook response: %s", data)
                    return False
        except Exception as exc:
            LOGGER.warning("Could not register Telegram webhook: %s", exc)
            return False


health_server = HealthServer()
