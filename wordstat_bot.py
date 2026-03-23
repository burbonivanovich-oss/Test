#!/usr/bin/env python3
"""
Wordstat → Telegram Bot
Collects data from Yandex Wordstat API across query clusters and sends a digest to Telegram.

Usage:
    python wordstat_bot.py [--config config.yaml]
    python wordstat_bot.py --daemon    # Run on schedule
"""

import argparse
import asyncio
import os
import sys
import textwrap
import time
from datetime import date, datetime, timedelta

import requests
import yaml
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load .env file if present (local dev); silently skip if python-dotenv not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import channel monitoring modules
from telegram_channel_monitor.channel_monitor import create_monitor
from telegram_channel_monitor.message_filter import MessageFilter
from telegram_channel_monitor.message_parser import parse_message_data
from telegram_channel_monitor.summary_formatter import (
    group_results_by_keyword,
    format_summary_with_pagination,
)


# ---------------------------------------------------------------------------
# Wordstat API client
# ---------------------------------------------------------------------------

class WordstatClient:
    def __init__(self, oauth_token: str, base_url: str = "https://api.wordstat.yandex.net"):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {oauth_token}",
            "Content-Type": "application/json;charset=utf-8",
        })
        self.base_url = base_url.rstrip("/")

    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        resp = self.session.post(url, json=payload, timeout=30)
        if not resp.ok:
            body = resp.text[:300].strip()
            raise requests.HTTPError(
                f"{resp.status_code} {resp.reason} — {body}",
                response=resp,
            )
        return resp.json()

    def get_regions_tree(self) -> dict:
        return self._post("/v1/getRegionsTree", {})

    @staticmethod
    def _fmt_phrase(phrase: str) -> str:
        return "+".join(phrase.strip().split())

    def top_requests(self, phrase: str, regions: list[int] = None,
                     devices: list[str] = None) -> list[dict]:
        payload: dict = {"phrase": self._fmt_phrase(phrase)}
        if regions:
            payload["regions"] = regions
        if devices and devices != ["all"]:
            payload["devices"] = devices
        data = self._post("/v1/topRequests", payload)
        return data.get("topRequests", [])

    def dynamics(self, phrase: str, period: str, from_date: str, to_date: str = None,
                 regions: list[int] = None, devices: list[str] = None) -> list[dict]:
        payload: dict = {"phrase": self._fmt_phrase(phrase), "period": period, "fromDate": from_date}
        if to_date:
            payload["toDate"] = to_date
        if regions:
            payload["regions"] = regions
        if devices and devices != ["all"]:
            payload["devices"] = devices
        data = self._post("/v1/dynamics", payload)
        return data.get("dynamics", [])

    def regions(self, phrase: str, region_type: str = "all",
                devices: list[str] = None) -> list[dict]:
        payload: dict = {"phrase": self._fmt_phrase(phrase), "regionType": region_type}
        if devices and devices != ["all"]:
            payload["devices"] = devices
        data = self._post("/v1/regions", payload)
        return data.get("regions", [])


# ---------------------------------------------------------------------------
# Report formatters — each returns a list of Markdown text lines
# ---------------------------------------------------------------------------

def _fmt_number(n: int | float) -> str:
    return f"{int(n):,}".replace(",", "\u202f")  # narrow no-break space as thousands sep


def format_top_requests(phrase: str, items: list[dict], top_n: int = 10) -> list[str]:
    lines = [f"🔍 <b>{escape_html(phrase)}</b> — топ запросов (30 дней)"]
    if not items:
        lines.append("  <i>нет данных</i>")
        return lines
    for i, item in enumerate(items[:top_n], 1):
        count = _fmt_number(item.get("count", 0))
        kw = escape_html(item.get("phrase", "—"))
        lines.append(f"  {i}. {kw} — {count}")
    return lines


def format_dynamics(phrase: str, items: list[dict]) -> list[str]:
    lines = [f"📈 <b>{escape_html(phrase)}</b> — динамика"]
    if not items:
        lines.append("  <i>нет данных</i>")
        return lines
    # Show last 6 data points
    for item in items[-6:]:
        d = item.get("date", "?")
        count = _fmt_number(item.get("count", 0))
        share = item.get("share", 0)
        lines.append(f"  {d}: {count} ({share:.4f}%)")
    # Trend: compare first vs last period
    if len(items) >= 2:
        first_count = items[0].get("count", 0)
        last_count = items[-1].get("count", 0)
        if first_count:
            delta = (last_count - first_count) / first_count * 100
            arrow = "↑" if delta >= 0 else "↓"
            lines.append(f"  Тренд: {arrow} {abs(delta):.1f}% к началу периода")
    return lines


def format_regions(phrase: str, items: list[dict], top_n: int = 5) -> list[str]:
    lines = [f"🗺 <b>{escape_html(phrase)}</b> — топ регионов (30 дней)"]
    if not items:
        lines.append("  <i>нет данных</i>")
        return lines
    sorted_items = sorted(items, key=lambda x: x.get("count", 0), reverse=True)
    for item in sorted_items[:top_n]:
        count = _fmt_number(item.get("count", 0))
        rid = escape_html(str(item.get("regionId", "?")))
        affinity = item.get("affinityIndex", 0)
        lines.append(f"  [{rid}] {count} запросов, affinity {affinity}%")
    return lines


# ---------------------------------------------------------------------------
# Cluster processor
# ---------------------------------------------------------------------------

def process_cluster(client: WordstatClient, cluster: dict) -> list[str]:
    name = cluster.get("name", "Без названия")
    method = cluster.get("method", "topRequests")
    phrases = cluster.get("phrases", [])
    regions = cluster.get("regions") or []
    devices = cluster.get("devices", ["all"])

    section: list[str] = [f"<b>━━ {escape_html(name)} ━━</b>"]

    for phrase in phrases:
        try:
            if method == "topRequests":
                items = client.top_requests(phrase, regions=regions, devices=devices)
                section += format_top_requests(phrase, items)

            elif method == "dynamics":
                period = cluster.get("period", "monthly")
                from_date = cluster.get("from_date") or _default_from_date(period)
                to_date = cluster.get("to_date")
                items = client.dynamics(phrase, period=period, from_date=from_date,
                                        to_date=to_date, regions=regions, devices=devices)
                section += format_dynamics(phrase, items)

            elif method == "regions":
                region_type = cluster.get("region_type", "all")
                items = client.regions(phrase, region_type=region_type, devices=devices)
                section += format_regions(phrase, items)

            else:
                section.append(f"  ⚠️ Неизвестный метод: {escape_html(method)}")

        except requests.HTTPError as exc:
            section.append(f"  ❌ Ошибка API для «{escape_html(phrase)}»: {escape_html(str(exc))}")
        except Exception as exc:  # noqa: BLE001
            section.append(f"  ❌ Ошибка для «{escape_html(phrase)}»: {escape_html(str(exc))}")

    return section


def _default_from_date(period: str) -> str:
    today = date.today()
    if period == "monthly":
        # first day of last month
        first_this = today.replace(day=1)
        last_month = first_this - timedelta(days=1)
        return last_month.replace(day=1).isoformat()
    if period == "weekly":
        # last Monday
        monday = today - timedelta(days=today.weekday())
        return (monday - timedelta(weeks=4)).isoformat()
    # daily — 30 days ago
    return (today - timedelta(days=30)).isoformat()


# ---------------------------------------------------------------------------
# Weekly analytics summary
# ---------------------------------------------------------------------------

def build_analytics_summary(client: WordstatClient, analytics: list[dict],
                             data_ready_weekday: int = 3) -> list[str]:
    """Build weekly analytics summary comparing current week vs previous week.

    The Wordstat API requires toDate for period=weekly to be a Sunday.
    We use the most recently completed Sunday as 'current week' and the
    Sunday before that as 'previous week'.

    Wordstat weekly data is typically published on Wednesday or Thursday.
    If today is before data_ready_weekday (0=Mon … 6=Sun, default 3=Thu),
    we shift the window back by one week to avoid returning all-zero rows.
    """
    today = date.today()
    # Most recently completed Sunday: Mon=0 → 1 day back, Sun=6 → 0 days back
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    prev_sunday = last_sunday - timedelta(weeks=1)

    # Fall back one week while fresh data hasn't been published yet
    if today.weekday() < data_ready_weekday:
        last_sunday -= timedelta(weeks=1)
        prev_sunday -= timedelta(weeks=1)

    # Label: Mon–Sun of the most recently completed week
    week_monday = last_sunday - timedelta(days=6)
    week_label = (
        f"{week_monday.strftime('%d.%m.%Y')} \u2013 {last_sunday.strftime('%d.%m.%Y')}"
    )

    # from_date: Monday of the previous week (ensures 2 weekly buckets are returned)
    from_date = (prev_sunday - timedelta(days=6)).isoformat()
    to_date = last_sunday.isoformat()  # must be a Sunday per API spec

    lines: list[str] = [f"📋 <b>Сводка за неделю {escape_html(week_label)}</b>", ""]

    for group in analytics:
        name = group.get("name", "Группа")
        phrases = group.get("phrases", [])
        regions = group.get("regions") or []
        devices = group.get("devices", ["all"])

        current_total = 0
        prev_total = 0
        errors: list[str] = []

        for phrase in phrases:
            try:
                items = client.dynamics(
                    phrase,
                    period="weekly",
                    from_date=from_date,
                    to_date=to_date,
                    regions=regions,
                    devices=devices,
                )
                if len(items) >= 2:
                    prev_total += items[-2].get("count", 0)
                    current_total += items[-1].get("count", 0)
                # len(items) == 1: can't determine which week, skip
            except requests.HTTPError as exc:
                errors.append(f"  ❌ Ошибка API для «{escape_html(phrase)}»: {escape_html(str(exc))}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"  ❌ Ошибка для «{escape_html(phrase)}»: {escape_html(str(exc))}")

        delta = current_total - prev_total
        if prev_total:
            pct = delta / prev_total * 100
            sign = "+" if delta >= 0 else ""
            change_str = (
                f"{sign}{delta:,} ({sign}{pct:.1f}%)"
                .replace(",", "\u202f")
            )
        else:
            change_str = "н/д"

        lines += [
            f"<b>{escape_html(name)}:</b>",
            f"  Текущая неделя: {_fmt_number(current_total)}",
            f"  Прошлая неделя: {_fmt_number(prev_total)}",
            f"  Изменение: {escape_html(change_str)}",
        ]
        lines += errors
        lines.append("")

    return lines


# ---------------------------------------------------------------------------
# Telegram sender
# ---------------------------------------------------------------------------

async def send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    # Telegram has a 4096-char limit per message; split if needed
    chunks = _split_message(text, limit=4000)
    for chunk in chunks:
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=30)
        if not resp.ok:
            print(f"Telegram error {resp.status_code}: {resp.text}", file=sys.stderr)
        resp.raise_for_status()


def _split_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


def escape_html(text: str) -> str:
    """Escape special chars for Telegram HTML mode."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(clusters_data: list[list[str]],
                 summary_lines: list[str] | None = None) -> str:
    today = date.today().strftime("%d.%m.%Y")
    header = [f"📊 <b>Wordstat дайджест</b> — {escape_html(today)}", ""]
    lines: list[str] = header
    if summary_lines:
        lines += summary_lines
        lines.append("")
    for section in clusters_data:
        lines += section
        lines.append("")
    return "\n".join(lines)


async def generate_report(client: WordstatClient, cfg: dict) -> str:
    """Generate the report text without sending."""
    clusters = cfg.get("clusters", [])
    analytics = cfg.get("analytics", [])
    wc_cfg = cfg.get("wordstat", {})
    data_ready_weekday = int(wc_cfg.get("data_ready_weekday", 3))

    summary_lines: list[str] = []
    if analytics:
        summary_lines = build_analytics_summary(client, analytics, data_ready_weekday)

    sections: list[list[str]] = []
    for cluster in clusters:
        sections.append(process_cluster(client, cluster))

    return build_report(sections, summary_lines)


# ---------------------------------------------------------------------------
# Channel monitoring
# ---------------------------------------------------------------------------

async def collect_channel_mentions(
    monitor,
    cfg: dict,
) -> list:
    """
    Collect keyword mentions from monitored channels.

    Args:
        monitor: ChannelMonitor instance
        cfg: Configuration dict with channel_monitor section

    Returns:
        List of (message_data, keyword) tuples
    """
    chan_cfg = cfg.get("channel_monitor", {})
    channels = chan_cfg.get("channels", [])
    keywords = chan_cfg.get("keywords", [])
    hours_lookback = chan_cfg.get("hours_lookback", 36)

    if not channels or not keywords:
        return []

    results: list = []

    for channel_info in channels:
        channel_name = channel_info.get("name", "Unknown")
        username = channel_info.get("username", "")
        channel_id = channel_info.get("channel_id")

        channel_identifier = username or channel_id
        if not channel_identifier:
            continue

        try:
            # Fetch messages from channel
            messages = await monitor.get_messages_from_channel(
                channel_identifier,
                limit=100,
            )

            if not messages:
                continue

            # Filter by timestamp and keywords
            filtered = MessageFilter.filter_messages(
                messages,
                keywords,
                hours_lookback,
            )

            # Parse message data
            for msg, keyword in filtered:
                msg_data = parse_message_data(msg, channel_name, username)
                results.append((msg_data, keyword))

        except Exception as exc:
            print(
                f"⚠️  Error processing channel {channel_name}: {exc}",
                file=sys.stderr,
            )
            continue

    return results


async def generate_channel_summary(monitor, cfg: dict) -> str:
    """
    Generate the channel monitoring summary.

    Args:
        monitor: ChannelMonitor instance
        cfg: Configuration dict

    Returns:
        Summary text
    """
    chan_cfg = cfg.get("channel_monitor", {})
    hours_lookback = chan_cfg.get("hours_lookback", 36)

    results = await collect_channel_mentions(monitor, cfg)

    if not results:
        return f"📊 <b>Мониторинг Telegram-каналов</b>\n\n🔍 <i>Упоминания ключевых слов не найдены за последние {hours_lookback} часов</i>"

    # Group by keyword
    grouped = group_results_by_keyword(results)

    # Format with pagination
    chunks = format_summary_with_pagination(grouped, hours_lookback)

    # Return combined text (will be split when sending)
    return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Telegram command handlers
# ---------------------------------------------------------------------------

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /report command."""
    client: WordstatClient = context.bot_data.get("wordstat_client")
    cfg: dict = context.bot_data.get("config")

    if not client or not cfg:
        await update.message.reply_text("❌ Бот не инициализирован. Попробуйте позже.")
        return

    try:
        await update.message.reply_text("⏳ Подготавливаю отчет...")
        report_text = await generate_report(client, cfg)
        await send_telegram(context.bot.token, str(update.effective_chat.id), report_text)
    except Exception as exc:
        await update.message.reply_text(f"❌ Ошибка: {escape_html(str(exc))}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "👋 Привет! Я — Wordstat дайджест бот.\n\n"
        "Используй /report для получения отчета.\n\n"
        "По расписанию я отправляю отчеты в группу автоматически."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(
        "📖 <b>Доступные команды:</b>\n\n"
        "/report — получить отчет сейчас\n"
        "/channels — мониторинг Telegram-каналов\n"
        "/start — справка\n"
        "/help — эта справка",
        parse_mode="HTML"
    )


async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /channels command."""
    monitor = context.bot_data.get("channel_monitor")
    cfg: dict = context.bot_data.get("config")

    if not monitor or not cfg:
        await update.message.reply_text("❌ Мониторинг каналов не инициализирован.")
        return

    chan_cfg = cfg.get("channel_monitor", {})
    if not chan_cfg.get("enabled"):
        await update.message.reply_text("❌ Мониторинг каналов отключен в конфиге.")
        return

    try:
        await update.message.reply_text("⏳ Анализирую каналы...")
        summary_text = await generate_channel_summary(monitor, cfg)

        # Split and send
        chunks = _split_message(summary_text, limit=4000)
        for chunk in chunks:
            await send_telegram(context.bot.token, str(update.effective_chat.id), chunk)

    except Exception as exc:
        await update.message.reply_text(f"❌ Ошибка: {escape_html(str(exc))}")


# ---------------------------------------------------------------------------
# Scheduled report (daemon mode)
# ---------------------------------------------------------------------------

async def schedule_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send scheduled report."""
    client: WordstatClient = context.bot_data.get("wordstat_client")
    cfg: dict = context.bot_data.get("config")
    chat_id: str = context.bot_data.get("chat_id")

    if not client or not cfg or not chat_id:
        return

    try:
        print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Sending scheduled report…")
        report_text = await generate_report(client, cfg)
        await send_telegram(context.bot.token, chat_id, report_text)
        print("Done ✓")
    except Exception as exc:
        print(f"ERROR during scheduled run: {exc}", file=sys.stderr)


async def schedule_channel_summary(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send scheduled channel monitoring summary."""
    monitor = context.bot_data.get("channel_monitor")
    cfg: dict = context.bot_data.get("config")
    chat_id: str = context.bot_data.get("chat_id")

    if not monitor or not cfg or not chat_id:
        return

    chan_cfg = cfg.get("channel_monitor", {})
    if not chan_cfg.get("enabled"):
        return

    try:
        print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Sending scheduled channel summary…")
        summary_text = await generate_channel_summary(monitor, cfg)
        chunks = _split_message(summary_text, limit=4000)
        for chunk in chunks:
            await send_telegram(context.bot.token, chat_id, chunk)
        print("Done ✓")
    except Exception as exc:
        print(f"ERROR during channel monitoring: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    parser = argparse.ArgumentParser(description="Wordstat → Telegram digest")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print report to stdout, don't send to Telegram")
    parser.add_argument("--daemon", action="store_true",
                        help="(deprecated, polling is now the default)")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    wc_cfg = cfg.get("wordstat", {})
    tg_cfg = cfg.get("telegram", {})
    clusters = cfg.get("clusters", [])

    # Secrets: env vars take priority over config.yaml values
    oauth_token = os.environ.get("WORDSTAT_OAUTH_TOKEN") or wc_cfg.get("oauth_token", "")
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or tg_cfg.get("bot_token", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or str(tg_cfg.get("chat_id", ""))

    if not oauth_token:
        print("ERROR: WORDSTAT_OAUTH_TOKEN not set (env var or config.yaml).", file=sys.stderr)
        sys.exit(1)
    if not args.dry_run and not bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set (env var or config.yaml).", file=sys.stderr)
        sys.exit(1)

    if not clusters:
        print("No clusters defined in config. Exiting.", file=sys.stderr)
        sys.exit(1)

    client = WordstatClient(
        oauth_token=oauth_token,
        base_url=wc_cfg.get("base_url", "https://api.wordstat.yandex.net"),
    )

    if args.dry_run:
        report_text = await generate_report(client, cfg)
        print("\n" + "=" * 60)
        print(report_text.replace("\\", ""))
        return

    # Polling + scheduled reports
    print(f"Starting bot with polling…")
    print(f"Using chat_id={chat_id!r}")

    app = Application.builder().token(bot_token).build()

    # Initialize channel monitor
    channel_monitor = None
    chan_cfg = cfg.get("channel_monitor", {})
    if chan_cfg.get("enabled"):
        channel_monitor = await create_monitor()
        if channel_monitor:
            print("✓ Channel monitor initialized")
        else:
            print("⚠️  Channel monitor failed to initialize (missing credentials)")

    # Store config and clients in bot_data for handlers to access
    app.bot_data["wordstat_client"] = client
    app.bot_data["channel_monitor"] = channel_monitor
    app.bot_data["config"] = cfg
    app.bot_data["chat_id"] = chat_id

    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("channels", channels_command))

    # Schedule reports
    sched = cfg.get("schedule", {})
    weekday = int(sched.get("weekday", 0))  # 0=Monday … 6=Sunday
    hour = int(sched.get("hour", 7))
    minute = int(sched.get("minute", 0))
    print(f"Scheduled report: every weekday={weekday} at {hour:02d}:{minute:02d} UTC")

    job_queue = app.job_queue
    job_queue.run_daily(schedule_report, time=datetime.min.replace(hour=hour, minute=minute).time(),
                       days=(weekday,), name="scheduled_report")

    # Schedule channel monitoring (if enabled)
    if channel_monitor and chan_cfg.get("enabled"):
        chan_sched = chan_cfg.get("schedule", {})
        chan_weekday = int(chan_sched.get("weekday", 1))
        chan_hour = int(chan_sched.get("hour", 10))
        chan_minute = int(chan_sched.get("minute", 0))
        print(f"Scheduled channel summary: every weekday={chan_weekday} at {chan_hour:02d}:{chan_minute:02d} UTC")
        job_queue.run_daily(schedule_channel_summary, time=datetime.min.replace(hour=chan_hour, minute=chan_minute).time(),
                           days=(chan_weekday,), name="scheduled_channel_summary")

    # Start polling
    print("Bot is listening for commands…")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=["message", "channel_post"])

    try:
        await asyncio.Event().wait()  # run forever
    except KeyboardInterrupt:
        print("\nShutting down…")
    finally:
        # Close channel monitor
        if channel_monitor:
            await channel_monitor.close()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
