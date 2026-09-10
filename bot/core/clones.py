# Licensed under the MIT License.

import os

from pyrogram import Client, raw

from .. import LOGGER
from .config import config
from .mongo import mongo


class CloneManager:
    def __init__(self):
        self.active: dict[int, Client] = {}
        self.profile_photo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets", "serena_profile_icon.png",
        )
        self.bot_short_description = (
            "SERENA downloads music and media from YouTube, Spotify, SoundCloud, "
            "Instagram, TikTok, and more — right in Telegram."
        )
        self.bot_description = (
            "Send a song name, or paste a link from YouTube, Spotify, SoundCloud, "
            "Instagram, Facebook, Threads, TikTok, Twitter/X, or Bluesky — I'll fetch "
            "it and send it right back to you.\n\n"
            "Works in groups and inline too.\n\n"
            "Powered by the open-source SERENA downloader: "
            "github.com/botstelegram7-cmyk/SERENA-DOWNLOADER"
        )

    async def load_all(self) -> None:
        docs = await mongo.all_clones()
        for doc in docs:
            try:
                await self.spinup(doc["_id"], doc["token"], persist=False)
            except Exception:
                LOGGER.exception("Failed to relaunch clone bot_id=%s", doc["_id"])
        if docs:
            LOGGER.info("Relaunched %d/%d cloned bot(s).", len(self.active), len(docs))

    async def spinup(
        self, bot_id: int, token: str, *, owner_id: int | None = None,
        username: str | None = None, persist: bool = True,
    ) -> Client:
        if bot_id in self.active:
            return self.active[bot_id]

        client = Client(
            f"clone_{bot_id}",
            api_id=config.api_id,
            api_hash=config.api_hash,
            bot_token=token,
            in_memory=True,
        )

        from ..handlers import attach_shared_handlers
        attach_shared_handlers(client)

        await client.start()
        self.active[bot_id] = client

        if persist:
            await mongo.save_clone(bot_id, owner_id, username, token)

        return client

    async def get_managed_bot_token(self, client: Client, bot_id: int) -> str:
        """Export a managed bot token across PyroTGFork releases.

        Some releases expose a convenience method while older releases expose
        the underlying MTProto method only. The raw fallback keeps the clone
        flow working with the pinned runtime dependency.
        """
        convenience = getattr(client, "get_managed_bot_token", None)
        if convenience is not None:
            return await convenience(bot_id)

        peer = await client.resolve_peer(bot_id)
        if isinstance(peer, raw.types.InputPeerUser):
            bot = raw.types.InputUser(user_id=peer.user_id, access_hash=peer.access_hash)
        elif isinstance(peer, raw.types.InputUser):
            bot = peer
        else:
            raise RuntimeError(f"Unable to resolve managed bot {bot_id}")

        exported = await client.invoke(
            raw.functions.bots.ExportBotToken(bot=bot, revoke=False)
        )
        token = getattr(exported, "token", None)
        if not token:
            raise RuntimeError(f"Telegram did not return a token for managed bot {bot_id}")
        return token

    async def stop(self, bot_id: int) -> None:
        client = self.active.pop(bot_id, None)
        if client:
            await client.stop()

    async def delete(self, bot_id: int) -> None:
        await self.stop(bot_id)
        await mongo.delete_clone(bot_id)

    async def set_branding(self, client: Client) -> None:
        """Apply SERENA branding to a managed bot where Telegram permits it."""
        try:
            await client.set_profile_photo(photo=self.profile_photo_path, for_my_bot=client.me.id)
        except Exception:
            LOGGER.exception("Failed to set profile photo for clone bot_id=%s", client.me.id)

        try:
            await client.set_bot_info_short_description(self.bot_short_description)
            await client.set_bot_info_description(self.bot_description)
        except Exception:
            LOGGER.exception("Failed to set bot description for clone bot_id=%s", client.me.id)


clones = CloneManager()
