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
            messages: List of Telethon Message objects
            keywords: List of keywords to search for (case-insensitive)

        Returns:
            List of Message objects containing keywords
        """
        filtered = []
        keywords_lower = [kw.lower() for kw in keywords]

        for msg in messages:
            if not msg.text:
                continue
            msg_text = msg.text.lower()
            for kw in keywords_lower:
                if kw in msg_text:
                    filtered.append((msg, kw))
                    break

        return filtered

    @staticmethod
    def filter_by_timestamp(messages: List, hours_lookback: int = 36) -> List:
        """
        Filter messages from the last N hours.

        Args:
            messages: List of Telethon Message objects
            hours_lookback: Number of hours to look back (default: 36)

        Returns:
            List of Message objects within the time window
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_lookback)

        filtered = []
        for msg in messages:
            if msg.date and msg.date.replace(tzinfo=None) >= cutoff_time:
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
            if msg.id not in seen:
                seen.add(msg.id)
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
