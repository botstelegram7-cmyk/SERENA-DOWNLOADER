# Copyright (c) 2026 tusar404
# Licensed under the MIT License.

import asyncio
from contextlib import suppress

from pyrogram import idle

from . import LOGGER, __bot_name__, __version__, app, mongo, setup_directories, yt_api
from .core.clones import clones
from .core.config import config
from .core.health import health_server


async def main() -> None:
    config.validate()
    LOGGER.info("Starting %s v%s...", __bot_name__, __version__)

    setup_directories()
    await mongo.connect()
    await yt_api.get_session()
    await app.start()

    try:
        from . import handlers

        await health_server.start()
        LOGGER.info("All modules loaded. Bot is up and running.")

        await clones.load_all()
        await idle()
    finally:
        LOGGER.info("Shutting down %s...", __bot_name__)
        with suppress(Exception):
            await health_server.stop()
        for bot_id in list(clones.active):
            with suppress(Exception):
                await clones.stop(bot_id)
        with suppress(Exception):
            await app.stop()
        with suppress(Exception):
            await yt_api.close()
        with suppress(Exception):
            await mongo.close()
        LOGGER.info("%s stopped.", __bot_name__)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
