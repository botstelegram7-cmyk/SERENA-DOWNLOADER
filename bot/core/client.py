# Copyright (c) 2026 tusar404
# Licensed under the MIT License.

from pyrogram import Client

from .config import config

app = Client(
    "serena",
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token,
    in_memory=True,
)
