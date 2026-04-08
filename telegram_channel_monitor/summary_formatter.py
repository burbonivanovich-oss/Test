"""
Formatter for building daily channel monitoring summaries.
"""

from datetime import datetime
from typing import List, Dict, Tuple

from .message_parser import escape_html, format_message_result


def group_results_by_keyword(
    results: List[Tuple]
) -> Dict[str, List]:
    """
    Group message results by keyword.

    Args:
        results: List of (message_data, keyword) tuples

    Returns:
        Dictionary mapping keyword -> list of message_data
    """
    grouped: Dict[str, List] = {}

    for message_data, keyword in results:
        if keyword not in grouped:
            grouped[keyword] = []
        grouped[keyword].append(message_data)

    # Sort each group by date (newest first)
    for keyword in grouped:
        grouped[keyword].sort(
            key=lambda m: m["date"] or datetime.min,
            reverse=True,
        )

    return grouped


def build_summary_text(
    grouped_results: Dict[str, List],
    hours_lookback: int = 36,
) -> str:
    """
    Build the complete summary text.

    Args:
        grouped_results: Dictionary from group_results_by_keyword()
        hours_lookback: Time window in hours (for header)

    Returns:
        Formatted summary text
    """
    if not grouped_results:
        return f"📊 <b>Мониторинг Telegram-каналов</b>\n\n🔍 <i>Упоминания ключевых слов не найдены за последние {hours_lookback} часов</i>"

    today = datetime.utcnow().strftime("%d.%m.%Y %H:%M UTC")
    lines = [
        f"📊 <b>Мониторинг Telegram-каналов</b> — {escape_html(today)}",
        f"⏱️  Период: последние {hours_lookback} часов",
        "",
    ]

    # Build sections by keyword
    for keyword in sorted(grouped_results.keys()):
        messages = grouped_results[keyword]

        lines.append(f"🔍 <b>Ключевое слово: \"{escape_html(keyword)}\"</b>")
        lines.append(f"   Найдено упоминаний: {len(messages)}")
        lines.append("")

        # Show top 5 results for each keyword
        for i, msg_data in enumerate(messages[:5], 1):
            formatted = format_message_result(msg_data, keyword, escape=True)
            lines.append(formatted)
            lines.append("")

        if len(messages) > 5:
            lines.append(f"   <i>… и еще {len(messages) - 5} упоминаний</i>")
            lines.append("")

    return "\n".join(lines)


def split_message(text: str, limit: int = 4000) -> List[str]:
    """
    Split long message into chunks (Telegram has 4096 char limit).

    Args:
        text: Message text
        limit: Maximum chunk size

    Returns:
        List of message chunks
    """
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break

        # Try to split at newline
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    return chunks


def format_summary_with_pagination(
    grouped_results: Dict[str, List],
    hours_lookback: int = 36,
) -> List[str]:
    """
    Format summary and split into paginated messages.

    Args:
        grouped_results: Dictionary from group_results_by_keyword()
        hours_lookback: Time window in hours

    Returns:
        List of message chunks ready to send
    """
    summary = build_summary_text(grouped_results, hours_lookback)
    chunks = split_message(summary)

    # Add pagination info if multiple chunks
    if len(chunks) > 1:
        for i, chunk in enumerate(chunks, 1):
            header = f"<b>[{i}/{len(chunks)}]</b>\n\n"
            chunks[i - 1] = header + chunk

    return chunks
