# Licensed under the MIT License.

from __future__ import annotations

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

        self._runner = web.AppRunner(application, access_log=None)
        await self._runner.setup()
        site = web.TCPSite(self._runner, host=config.host, port=config.port)
        await site.start()
        LOGGER.info("Health server listening on %s:%s", config.host, config.port)

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


health_server = HealthServer()
