"""
RSS-Hub based Telegram channel monitor.

Alternative to Telethon that doesn't require SMS authentication.
Uses public RSS feeds from RSSHub instances to monitor Telegram channels.
"""

import aiohttp
import asyncio
import ssl
import certifi
import feedparser
import logging
import re
import html
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

RSSHUB_INSTANCES = [
    "https://rsshub.app",
    "https://rsshub.rssforever.com",
    "https://rsshub.uneasy.win",
]


def clean_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities."""
    # Remove tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class RSSChannelMonitor:
    """Monitor Telegram channels via RSS feeds."""

    def __init__(self):
        """Initialize the RSS monitor."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def connect(self) -> None:
        """Create aiohttp session."""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def disconnect(self) -> None:
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def close(self) -> None:
        """Alias for disconnect."""
        await self.disconnect()

    async def _fetch_rss_text(self, rss_url: str) -> Optional[str]:
        """
        Fetch RSS feed content from a single instance.

        Args:
            rss_url: Full RSS URL

        Returns:
            Feed content or None if failed
        """
        if not self.session:
            await self.connect()

        instance = rss_url.split('/')[2]  # Extract domain

        try:
            async with self.session.get(
                rss_url,
                ssl=self.ssl_context,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    logger.debug(f"✅ Fetched RSS from {instance}")
                    return text
                else:
                    logger.warning(f"⚠️  {instance} returned {resp.status}")
                    return None

        except asyncio.TimeoutError:
            logger.warning(f"⏱️  Timeout connecting to {instance}")
            return None
        except Exception as e:
            logger.warning(f"❌ Error fetching from {instance}: {e}")
            return None

    async def _get_messages_from_feed(
        self,
        channel_identifier: str,
        hours_lookback: int = 36,
    ) -> List[Dict]:
        """
        Fetch messages from Telegram channel via RSS.

        Args:
            channel_identifier: Channel username (with or without @)
            hours_lookback: How many hours back to fetch

        Returns:
            List of message dictionaries
        """
        if not self.session:
            await self.connect()

        clean_name = channel_identifier.lstrip('@')
        messages = []
        now = datetime.now()
        cutoff = now - timedelta(hours=hours_lookback)

        # Try each RSSHub instance
        success = False
        feed_text = None

        for instance in RSSHUB_INSTANCES:
            rss_url = f"{instance}/telegram/channel/{clean_name}"
            logger.debug(f"Trying {instance} for @{clean_name}")

            feed_text = await self._fetch_rss_text(rss_url)
            if feed_text:
                success = True
                break

        if not success:
            logger.warning(f"⚠️  Could not fetch RSS for @{clean_name}")
            return []

        # Parse feed
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, feed_text)

        if hasattr(feed, 'bozo_exception') and feed.bozo_exception:
            logger.error(f"❌ Parse error for @{clean_name}: {feed.bozo_exception}")
            return []

        if not feed.entries:
            logger.warning(f"⚠️  No entries in RSS for @{clean_name}")
            return []

        # Extract messages within time window
        for entry in feed.entries:
            try:
                # Get timestamp
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                else:
                    continue

                # Skip old messages
                if published < cutoff:
                    continue

                # Extract text
                raw_text = entry.title + ' ' + entry.get('summary', '')
                cleaned_text = clean_html(raw_text)

                # Build message dict
                msg = {
                    'id': hash(entry.title),  # Pseudo-ID
                    'text': cleaned_text,
                    'date': published,
                    'link': entry.link if hasattr(entry, 'link') else f"https://t.me/{clean_name}",
                    'title': entry.title,
                }
                messages.append(msg)

            except Exception as e:
                logger.debug(f"Error parsing entry: {e}")
                continue

        logger.info(f"📨 Fetched {len(messages)} messages from @{clean_name}")
        return messages

    async def get_messages_from_channel(
        self,
        channel_identifier: str,
        limit: int = 100,
        hours_lookback: int = 36,
    ) -> List[Dict]:
        """
        Get recent messages from a Telegram channel.

        Args:
            channel_identifier: Channel username (@example) or name
            limit: Maximum messages to return (ignored, RSS feeds return what they have)
            hours_lookback: Hours to look back (default: 36)

        Returns:
            List of message dictionaries
        """
        messages = await self._get_messages_from_feed(
            channel_identifier,
            hours_lookback=hours_lookback,
        )
        return messages[:limit] if messages else []


async def create_rss_monitor() -> RSSChannelMonitor:
    """
    Create and initialize an RSSChannelMonitor.

    Returns:
        Initialized RSSChannelMonitor instance
    """
    monitor = RSSChannelMonitor()
    try:
        await monitor.connect()
        return monitor
    except Exception as e:
        logger.error(f"Failed to initialize RSS monitor: {e}")
        return None
