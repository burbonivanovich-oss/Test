"""
RSS-Hub based Telegram channel monitor.

Alternative to Telethon that doesn't require SMS authentication.
Uses public RSS feeds from RSSHub instances to monitor Telegram channels.
"""

import aiohttp
import asyncio
import hashlib
import logging
import re
import html
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

RSSHUB_INSTANCES = [
    "https://rsshub.app",
    "https://rsshub.rssforever.com",
    "https://rsshub.uneasy.win",
]


def clean_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities."""
    if not text:
        return ""
    # Remove tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_rss_feed(feed_xml: str) -> List[Dict]:
    """
    Parse RSS feed XML using built-in xml.etree.

    Args:
        feed_xml: XML content as string

    Returns:
        List of entry dictionaries
    """
    entries = []
    try:
        root = ET.fromstring(feed_xml)

        # Handle both RSS and Atom formats
        # RSS: /rss/channel/item
        # Atom: /feed/entry

        # Try RSS format
        for item in root.findall('.//item'):
            entry = {}

            # Title
            title_el = item.find('title')
            entry['title'] = title_el.text if title_el is not None else ''

            # Description/Summary
            desc_el = item.find('description')
            entry['summary'] = desc_el.text if desc_el is not None else ''

            # Link
            link_el = item.find('link')
            entry['link'] = link_el.text if link_el is not None else ''

            # PubDate
            pubdate_el = item.find('pubDate')
            if pubdate_el is not None and pubdate_el.text:
                try:
                    # Try to parse RFC 2822 format (RSS standard)
                    from email.utils import parsedate_to_datetime
                    entry['pubdate'] = parsedate_to_datetime(pubdate_el.text)
                except:
                    entry['pubdate'] = None
            else:
                entry['pubdate'] = None

            if entry['title']:  # Only add if has title
                entries.append(entry)

        # If no RSS items, try Atom format
        if not entries:
            for entry_el in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                entry = {}

                # Title
                title_el = entry_el.find('{http://www.w3.org/2005/Atom}title')
                entry['title'] = title_el.text if title_el is not None else ''

                # Summary/Content — each element may be None independently
                summary_el = entry_el.find('{http://www.w3.org/2005/Atom}summary')
                content_el = entry_el.find('{http://www.w3.org/2005/Atom}content')
                summary_text = summary_el.text if summary_el is not None else None
                content_text = content_el.text if content_el is not None else None
                entry['summary'] = summary_text or content_text or ''

                # Link
                link_el = entry_el.find('{http://www.w3.org/2005/Atom}link')
                if link_el is not None:
                    entry['link'] = link_el.get('href', '')
                else:
                    entry['link'] = ''

                # Published
                published_el = entry_el.find('{http://www.w3.org/2005/Atom}published')
                if published_el is not None and published_el.text:
                    try:
                        # ISO 8601 format
                        entry['pubdate'] = datetime.fromisoformat(published_el.text.replace('Z', '+00:00'))
                    except:
                        entry['pubdate'] = None
                else:
                    entry['pubdate'] = None

                if entry['title']:
                    entries.append(entry)

    except Exception as e:
        logger.error(f"Error parsing RSS/Atom feed: {e}")
        return []

    return entries


class RSSChannelMonitor:
    """Monitor Telegram channels via RSS feeds."""

    def __init__(self):
        """Initialize the RSS monitor."""
        self.session: Optional[aiohttp.ClientSession] = None
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

        instance = urlparse(rss_url).netloc

        try:
            async with self.session.get(
                rss_url,
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
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=hours_lookback)

        # Try each RSSHub instance
        feed_text = None

        for instance in RSSHUB_INSTANCES:
            rss_url = f"{instance}/telegram/channel/{clean_name}"
            logger.debug(f"Trying {instance} for @{clean_name}")

            feed_text = await self._fetch_rss_text(rss_url)
            if feed_text:
                break

        if not feed_text:
            logger.warning(f"⚠️  Could not fetch RSS for @{clean_name}")
            return []

        # Parse feed
        entries = parse_rss_feed(feed_text)

        if not entries:
            logger.warning(f"⚠️  No entries in RSS for @{clean_name}")
            return []

        # Extract messages within time window
        for entry in entries:
            try:
                # Get timestamp
                pubdate = entry.get('pubdate')
                if not pubdate:
                    continue

                # Handle timezone-naive datetime
                if pubdate.tzinfo is not None:
                    pubdate = pubdate.replace(tzinfo=None)

                # Skip old messages
                if pubdate < cutoff:
                    continue

                # Extract text
                raw_text = (entry.get('title', '') or '') + ' ' + (entry.get('summary', '') or '')
                cleaned_text = clean_html(raw_text)

                if not cleaned_text:
                    continue

                # Build message dict
                # Use MD5 of the link as a stable integer ID.
                # Python's built-in hash() is randomized per-process (PYTHONHASHSEED),
                # so identical links produce different IDs across restarts — broken dedup.
                link = entry.get('link', '') or f"https://t.me/{clean_name}"
                stable_id = int(hashlib.md5(link.encode()).hexdigest(), 16)
                msg = {
                    'id': stable_id,
                    'text': cleaned_text,
                    'date': pubdate,
                    'link': link,
                    'title': entry.get('title', ''),
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
