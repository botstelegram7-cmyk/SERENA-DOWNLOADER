# Licensed under the MIT License.


import asyncio
import time

import aiohttp

from .. import LOGGER
from ..core.config import config


class YTAPIError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class YTAPIClient:
    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
        self._key_cursor = 0
        self.request_timeout = 60.0
        self.request_retries = 2
        self.job_poll_interval = 2.0
        self.job_poll_timeout = 180.0
        self.social_platforms = {
            "instagram": "download_instagram",
            "facebook": "download_facebook",
            "threads": "download_threads",
            "bluesky": "download_bluesky",
            "tiktok": "download_tiktok",
            "twitter": "download_twitter",
            "pinterest": "download_pinterest",
            "reddit": "download_reddit",
        }

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            LOGGER.warning("YTAPIClient session was not open; opening it lazily.")
            return await self.get_session()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            LOGGER.info("YTAPIClient session closed.")
        self._session = None

    def _next_api_key(self) -> str:
        keys = config.api_keys
        if not keys:
            return ""
        key = keys[self._key_cursor % len(keys)]
        self._key_cursor += 1
        return key

    async def _get(self, path: str, params: dict) -> dict:
        session = await self._get_session()
        base_params = {
            k: ("true" if v else "false") if isinstance(v, bool) else v
            for k, v in params.items()
        }
        url = f"{config.api_url}{path}"
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        api_keys = config.api_keys

        if not api_keys:
            raise YTAPIError("No Arc API key is configured")

        last_error: Exception | None = None
        total_keys = len(api_keys)

        # A 401/403/429 or repeated transport failure moves to the next key.
        # 400/404/422 are request/content errors and are returned immediately.
        for key_attempt in range(total_keys):
            api_key = self._next_api_key()
            for attempt in range(1, self.request_retries + 1):
                clean_params = {**base_params, "api_key": api_key}
                try:
                    async with session.get(url, params=clean_params, timeout=timeout) as r:
                        try:
                            data = await r.json()
                        except Exception:
                            response_text = await r.text()
                            raise YTAPIError(
                                f"Non-JSON response ({r.status}): {response_text[:200]}",
                                status=r.status,
                            )

                        if r.status != 200:
                            detail = data.get("detail") if isinstance(data, dict) else data
                            raise YTAPIError(str(detail) or f"HTTP {r.status}", status=r.status)

                        return data
                except YTAPIError as exc:
                    last_error = exc
                    if exc.status in {400, 404, 422}:
                        raise
                    if attempt < self.request_retries:
                        LOGGER.warning(
                            "Arc API request failed for %s (attempt %d/%d, status=%s); retrying key",
                            path, attempt, self.request_retries, exc.status,
                        )
                        await asyncio.sleep(1.5)
                        continue
                    break
                except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
                    last_error = exc
                    if attempt < self.request_retries:
                        LOGGER.warning(
                            "Request to %s timed out/failed (attempt %d/%d); retrying key",
                            path, attempt, self.request_retries,
                        )
                        await asyncio.sleep(1.5)
                        continue
                    break

            if key_attempt < total_keys - 1:
                LOGGER.warning(
                    "Arc API key attempt %d/%d failed for %s; trying the next configured key",
                    key_attempt + 1, total_keys, path,
                )

        if isinstance(last_error, YTAPIError):
            raise last_error
        raise YTAPIError(f"Request to {path} failed with all configured API keys: {last_error}")

    async def search_youtube(self, query: str, limit: int = 5) -> list[dict]:
        data = await self._get("/youtube/v2/search", {"query": query, "limit": limit})
        return data.get("results", [])

    async def get_youtube_playlist(self, link: str, limit: int = 100) -> dict:
        return await self._get("/youtube/v2/playlist", {"link": link, "limit": limit})

    async def download_youtube(self, query: str, is_video: bool = False) -> dict:
        data = await self._get("/youtube/v2/download", {"query": query, "isVideo": is_video})

        if data.get("job_id") is None:
            result = data.get("result")
            if not result or not result.get("success"):
                raise YTAPIError("Download failed: empty result from cache lookup")
            return result

        return await self._poll_job(data["job_id"])

    async def _poll_job(self, job_id: str) -> dict:
        deadline = time.monotonic() + self.job_poll_timeout
        while time.monotonic() < deadline:
            data = await self._get("/youtube/jobStatus", {"job_id": job_id})
            job = data.get("job", {})
            status = job.get("status")

            if status == "done":
                result = job.get("result")
                if not result or not result.get("success"):
                    raise YTAPIError(f"Download failed: {result}")
                return result
            if status == "error":
                raise YTAPIError(job.get("error") or "Download job failed")

            await asyncio.sleep(self.job_poll_interval)

        raise YTAPIError("Timed out waiting for download to finish")

    async def download_spotify(self, link: str) -> dict:
        data = await self._get("/spotify/download", {"link": link})
        if not data.get("success"):
            raise YTAPIError(data.get("error") or "Spotify download failed")
        return data

    async def get_spotify_playlist(self, link: str) -> dict:
        return await self._get("/spotify/playlist", {"link": link})

    async def download_soundcloud(self, query: str) -> dict:
        data = await self._get("/soundcloud/download", {"query": query})
        return data.get("result", {})

    async def _download_social(self, path: str, url: str) -> dict:
        return await self._get(path, {"url": url})

    async def download_instagram(self, url: str) -> dict:
        return await self._download_social("/instagram/download", url)

    async def download_facebook(self, url: str) -> dict:
        return await self._download_social("/facebook/download", url)

    async def download_threads(self, url: str) -> dict:
        return await self._download_social("/threads/download", url)

    async def download_bluesky(self, url: str) -> dict:
        return await self._download_social("/bluesky/download", url)

    async def download_tiktok(self, url: str) -> dict:
        return await self._download_social("/tiktok/download", url)

    async def download_twitter(self, url: str) -> dict:
        return await self._download_social("/twitter/download", url)

    async def download_pinterest(self, url: str) -> dict:
        return await self._download_social("/pinterest/download", url)

    async def download_reddit(self, url: str) -> dict:
        return await self._download_social("/reddit/download", url)

    async def download_terabox(self, url: str) -> dict:
        return await self._get("/terabox/download", {"url": url})

    async def search_applemusic(self, url: str) -> dict:
        return await self._get("/applemusic/search", {"url": url})

    async def download_applemusic(self, url: str) -> dict:
        return await self._get("/applemusic/download", {"url": url})

    async def search_jiosaavn(self, url: str) -> dict:
        return await self._get("/jiosaavn/search", {"url": url})

    async def download_jiosaavn(self, url: str) -> dict:
        return await self._get("/jiosaavn/download", {"url": url})


yt_api = YTAPIClient()
