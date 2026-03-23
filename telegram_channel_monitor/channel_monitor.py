"""
Telethon-based Telegram channel monitor.
"""

import os
import sys
from typing import List, Optional

from telethon import TelegramClient
from telethon.errors import ChannelPrivateError, ChannelInvalidError


class ChannelMonitor:
    """Manages Telethon client for monitoring Telegram channels."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_string: str,
    ):
        """
        Initialize the channel monitor.

        Args:
            api_id: Telegram API ID from https://my.telegram.org/apps
            api_hash: Telegram API hash from https://my.telegram.org/apps
            session_string: Session string (generated during authentication)
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.client: Optional[TelegramClient] = None

    async def connect(self) -> None:
        """Connect to Telegram."""
        if self.client is None:
            self.client = TelegramClient(
                self.session_string,
                self.api_id,
                self.api_hash,
            )
            await self.client.connect()

    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
            self.client = None

    async def _ensure_connected(self) -> None:
        """Ensure client is connected."""
        if self.client is None:
            await self.connect()
        elif not await self.client.is_user_authorized():
            await self.connect()

    async def get_messages_from_channel(
        self,
        channel_identifier: str,
        limit: int = 100,
    ) -> List:
        """
        Get recent messages from a channel.

        Args:
            channel_identifier: Channel username (@example) or ID
            limit: Maximum number of messages to fetch

        Returns:
            List of Message objects, or empty list on error
        """
        await self._ensure_connected()

        try:
            # Normalize channel identifier
            if isinstance(channel_identifier, str):
                channel_id = channel_identifier.lstrip("@")
            else:
                channel_id = channel_identifier

            # Fetch messages
            messages = await self.client.get_messages(
                channel_id,
                limit=limit,
            )

            return messages if messages else []

        except (ChannelPrivateError, ChannelInvalidError) as e:
            print(
                f"⚠️  Cannot access channel {channel_identifier}: {e}",
                file=sys.stderr,
            )
            return []

        except Exception as e:
            print(
                f"❌ Error fetching messages from {channel_identifier}: {e}",
                file=sys.stderr,
            )
            return []

    async def get_channel_entity(self, channel_identifier: str):
        """
        Get channel entity (for extracting display name, etc).

        Args:
            channel_identifier: Channel username (@example) or ID

        Returns:
            Channel entity or None on error
        """
        await self._ensure_connected()

        try:
            # Normalize
            if isinstance(channel_identifier, str):
                channel_id = channel_identifier.lstrip("@")
            else:
                channel_id = channel_identifier

            entity = await self.client.get_entity(channel_id)
            return entity

        except Exception as e:
            print(
                f"⚠️  Cannot get entity for {channel_identifier}: {e}",
                file=sys.stderr,
            )
            return None

    async def close(self) -> None:
        """Close the client connection."""
        await self.disconnect()


async def create_monitor(
    api_id: Optional[int] = None,
    api_hash: Optional[str] = None,
    session_string: Optional[str] = None,
) -> Optional[ChannelMonitor]:
    """
    Create and initialize a ChannelMonitor from environment or provided values.

    Args:
        api_id: API ID (defaults to TELETHON_API_ID env var)
        api_hash: API hash (defaults to TELETHON_API_HASH env var)
        session_string: Session string (defaults to TELETHON_SESSION_STRING env var)

    Returns:
        Initialized ChannelMonitor or None if credentials missing
    """
    api_id = api_id or int(os.environ.get("TELETHON_API_ID", 0))
    api_hash = api_hash or os.environ.get("TELETHON_API_HASH", "")
    session_string = session_string or os.environ.get("TELETHON_SESSION_STRING", "")

    if not api_id or not api_hash or not session_string:
        print(
            "ERROR: Missing Telethon credentials. Set TELETHON_API_ID, "
            "TELETHON_API_HASH, and TELETHON_SESSION_STRING environment variables.",
            file=sys.stderr,
        )
        return None

    monitor = ChannelMonitor(api_id, api_hash, session_string)
    try:
        await monitor.connect()
        return monitor
    except Exception as e:
        print(f"ERROR: Failed to connect to Telegram: {e}", file=sys.stderr)
        return None
