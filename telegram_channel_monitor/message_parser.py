"""
Message parsing logic for Telegram channel monitoring.
"""

from typing import Optional, Tuple


def escape_html(text: str) -> str:
    """Escape special chars for Telegram HTML mode."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_message_link(channel_username: Optional[str], message_id: int) -> str:
    """
    Generate a link to a Telegram message.

    Args:
        channel_username: Channel username (without @) or None for private channels
        message_id: Message ID

    Returns:
        URL to the message or fallback text
    """
    if channel_username:
        # Remove @ if present
        username = channel_username.lstrip("@")
        return f"https://t.me/{username}/{message_id}"
    else:
        # For private channels, we can't generate a public link
        return f"[Message {message_id}]"


def get_message_preview(text: str, max_length: int = 300) -> str:
    """
    Get a preview of message text.

    Args:
        text: Full message text
        max_length: Maximum preview length

    Returns:
        Truncated text with ellipsis if needed
    """
    if not text:
        return "(пусто)"

    text = text.strip()
    if len(text) <= max_length:
        return text

    # Truncate at word boundary
    preview = text[:max_length]
    last_space = preview.rfind(" ")
    if last_space > max_length - 50:  # Only if space is reasonably close
        preview = preview[:last_space]

    return preview + "…"


def parse_message_data(msg, channel_name: str, channel_username: Optional[str]) -> dict:
    """
    Extract relevant data from a message object.

    Handles both Telethon Message objects and dict-based messages from RSS.

    Args:
        msg: Telethon Message object or dict with message data
        channel_name: Display name of the channel
        channel_username: Username of the channel (for link generation)

    Returns:
        Dictionary with message data
    """
    # Handle dict-based messages (from RSS)
    if isinstance(msg, dict):
        msg_id = msg.get('id', 0)
        text = msg.get('text', '')
        date = msg.get('date')
        link = msg.get('link') or get_message_link(channel_username, msg_id)
        has_media = msg.get('has_media', False)
    else:
        # Handle Telethon Message objects
        msg_id = msg.id
        text = msg.text or ""
        date = msg.date
        link = get_message_link(channel_username, msg_id)
        has_media = bool(msg.media) if hasattr(msg, 'media') else False

    return {
        "message_id": msg_id,
        "channel_name": channel_name,
        "channel_username": channel_username,
        "link": link,
        "text": text,
        "preview": get_message_preview(text),
        "date": date,
        "has_media": has_media,
    }


def format_message_result(
    message_data: dict,
    keyword: str,
    escape: bool = True
) -> str:
    """
    Format a single message result for display.

    Args:
        message_data: Dictionary from parse_message_data()
        keyword: The keyword that matched
        escape: Whether to escape HTML (default: True)

    Returns:
        Formatted message string
    """
    if escape:
        channel_name = escape_html(message_data["channel_name"])
        preview = escape_html(message_data["preview"])
    else:
        channel_name = message_data["channel_name"]
        preview = message_data["preview"]

    link = message_data["link"]
    date = message_data["date"].strftime("%Y-%m-%d %H:%M UTC") if message_data["date"] else "—"

    result = f"""📱 <b>{channel_name}</b>
🔗 Ссылка: {link}
📝 Текст: {preview}
🕐 Дата: {date}"""

    return result
