"""
Direct RSS/Atom feed monitor for arbitrary web feeds.

Fetches any public RSS or Atom feed by URL and returns messages in the same
dict format used by RSSChannelMonitor, so all downstream filters and formatters
work without modification.
"""

import asyncio
import hashlib
import logging

import aiohttp

from .rss_channel_monitor import clean_html, parse_rss_feed

logger = logging.getLogger(__name__)


class RSSFeedMonitor:
    """Fetch and filter arbitrary RSS/Atom feeds by URL."""

    def __init__(self) -> None:
        self.session: aiohttp.ClientSession | None = None
        self.headers = {"User-Agent": "Mozilla/5.0 (compatible; FeedBot/1.0)"}

    async def connect(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None

    async def _fetch(self, url: str) -> str | None:
        if not self.session:
            await self.connect()
        try:
            async with self.session.get(
                url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 200:
                    return await resp.text()
                logger.warning("Feed %s returned %s", url, resp.status)
        except asyncio.TimeoutError:
            logger.warning("Timeout fetching %s", url)
        except Exception as exc:
            logger.warning("Error fetching %s: %s", url, exc)
        return None

    async def get_messages(self, name: str, url: str) -> list[dict]:
        """
        Fetch a feed and return all entries as message dicts.

        Time filtering is intentionally left to MessageFilter (same as channels)
        so hours_lookback from config is applied uniformly downstream.
        """
        text = await self._fetch(url)
        if not text:
            return []

        entries = parse_rss_feed(text)
        if not entries:
            logger.warning("No entries parsed from %s", name)
            return []

        messages = []
        for entry in entries:
            raw_text = (entry.get("title") or "") + " " + (entry.get("summary") or "")
            cleaned = clean_html(raw_text)
            if not cleaned:
                continue

            link = entry.get("link") or url
            stable_id = int(hashlib.md5(link.encode()).hexdigest(), 16)
            messages.append(
                {
                    "id": stable_id,
                    "text": cleaned,
                    "date": entry.get("pubdate"),
                    "link": link,
                    "title": entry.get("title", ""),
                }
            )

        logger.info("Fetched %d entries from %s", len(messages), name)
        return messages
