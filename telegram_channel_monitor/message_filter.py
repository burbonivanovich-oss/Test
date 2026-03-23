"""
Message filtering logic for Telegram channel monitoring.
"""

from datetime import datetime, timedelta
from typing import List


class MessageFilter:
    """Filter messages by keyword and timestamp."""

    @staticmethod
    def filter_by_keyword(messages: List, keywords: List[str]) -> List:
        """
        Filter messages that contain any of the keywords.

        Args:
            messages: List of Message objects (Telethon or dict-based from RSS)
            keywords: List of keywords to search for (case-insensitive)

        Returns:
            List of (Message, keyword) tuples containing keywords
        """
        filtered = []
        keywords_lower = [kw.lower() for kw in keywords]

        for msg in messages:
            # Handle both Telethon Message objects and dict-based messages
            if isinstance(msg, dict):
                msg_text = msg.get('text', '')
            else:
                msg_text = msg.text if hasattr(msg, 'text') else ''

            if not msg_text:
                continue

            msg_text_lower = msg_text.lower()
            for kw in keywords_lower:
                if kw in msg_text_lower:
                    filtered.append((msg, kw))
                    break

        return filtered

    @staticmethod
    def filter_by_timestamp(messages: List, hours_lookback: int = 36) -> List:
        """
        Filter messages from the last N hours.

        Args:
            messages: List of Message objects (Telethon or dict-based)
            hours_lookback: Number of hours to look back (default: 36)

        Returns:
            List of Message objects within the time window
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_lookback)

        filtered = []
        for msg in messages:
            # Handle both Telethon Message objects and dict-based messages
            if isinstance(msg, dict):
                msg_date = msg.get('date')
            else:
                msg_date = msg.date if hasattr(msg, 'date') else None

            if msg_date:
                # Handle timezone-aware datetime
                if hasattr(msg_date, 'replace'):
                    msg_date_naive = msg_date.replace(tzinfo=None)
                else:
                    msg_date_naive = msg_date

                if msg_date_naive >= cutoff_time:
                    filtered.append(msg)

        return filtered

    @staticmethod
    def deduplicate_messages(messages: List) -> List:
        """
        Remove duplicate messages by ID.

        Args:
            messages: List of messages (possibly with tuples (msg, keyword))

        Returns:
            List of unique messages
        """
        seen = set()
        unique = []

        for item in messages:
            msg = item[0] if isinstance(item, tuple) else item

            # Get message ID (works with both Telethon and dict-based)
            if isinstance(msg, dict):
                msg_id = msg.get('id')
            else:
                msg_id = msg.id if hasattr(msg, 'id') else None

            if msg_id and msg_id not in seen:
                seen.add(msg_id)
                unique.append(item)

        return unique

    @staticmethod
    def filter_messages(messages: List, keywords: List[str], hours_lookback: int = 36) -> List:
        """
        Apply all filters in sequence.

        Args:
            messages: List of Telethon Message objects
            keywords: List of keywords to search for
            hours_lookback: Number of hours to look back

        Returns:
            List of filtered messages with keywords
        """
        # Filter by timestamp first
        by_time = MessageFilter.filter_by_timestamp(messages, hours_lookback)

        # Then filter by keyword
        by_keyword = MessageFilter.filter_by_keyword(by_time, keywords)

        # Deduplicate
        unique = MessageFilter.deduplicate_messages(by_keyword)

        return unique
