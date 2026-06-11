#!/usr/bin/env python3
"""
Bot launcher.

Starts two independent features in a single bot process:
  1. Wordstat feature  — /report command + weekly scheduled digest
  2. Channels feature  — /channels command + daily channel monitoring digest
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime

import aiohttp
import yaml
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from wordstat import WordstatClient, generate_report, generate_daily_compact_report, escape_html
from telegram_channel_monitor.channel_monitor import create_monitor
from telegram_channel_monitor.message_filter import MessageFilter
from telegram_channel_monitor.message_parser import parse_message_data
from telegram_channel_monitor.summary_formatter import (
    group_results_by_keyword,
    format_summary_with_pagination,
)
from telegram_channel_monitor.rss_feed_monitor import RSSFeedMonitor


# ---------------------------------------------------------------------------
# Shared Telegram utilities
# ---------------------------------------------------------------------------

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


async def send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    """Send text to Telegram (non-blocking, splits long messages automatically)."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with aiohttp.ClientSession() as session:
        for chunk in _split_message(text):
            async with session.post(
                url,
                json={"chat_id": chat_id, "text": chunk,
                      "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if not resp.ok:
                    print(f"Telegram error {resp.status}: {await resp.text()}", file=sys.stderr)
                resp.raise_for_status()


async def send_telegram_photo(bot_token: str, chat_id: str, photo_buf, caption: str = "") -> None:
    """Send a PNG BytesIO as a photo via Telegram Bot API (multipart/form-data)."""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field("chat_id", chat_id)
        data.add_field("parse_mode", "HTML")
        if caption:
            data.add_field("caption", caption[:1024])
        data.add_field("photo", photo_buf, filename="chart.png", content_type="image/png")
        async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if not resp.ok:
                print(f"Telegram photo error {resp.status}: {await resp.text()}", file=sys.stderr)
            resp.raise_for_status()


# ---------------------------------------------------------------------------
# Feature 1 — Wordstat
# ---------------------------------------------------------------------------

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /report — build and send a Wordstat digest on demand."""
    print(f"[COMMAND] /report from user {update.effective_user.id}")
    client: WordstatClient = context.bot_data.get("wordstat_client")
    cfg: dict = context.bot_data.get("config")
    if not client or not cfg:
        await update.message.reply_text("❌ Бот не инициализирован. Попробуйте позже.")
        return
    try:
        await update.message.reply_text("⏳ Подготавливаю отчет...")
        report_text = await generate_report(client, cfg)
        await send_telegram(context.bot.token, str(update.effective_chat.id), report_text)
        print("[OK] /report sent")
    except Exception as exc:
        print(f"[ERROR] /report: {exc}", file=sys.stderr)
        await update.message.reply_text(f"❌ Ошибка: {escape_html(str(exc))}")


async def dynamics_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dynamics — send daily compact Wordstat report on demand."""
    print(f"[COMMAND] /dynamics from user {update.effective_user.id}")
    client: WordstatClient = context.bot_data.get("wordstat_client")
    cfg: dict = context.bot_data.get("config")
    if not client or not cfg:
        await update.message.reply_text("❌ Бот не инициализирован. Попробуйте позже.")
        return
    try:
        await update.message.reply_text("⏳ Подготавливаю ежедневную сводку...")
        report, chart = await generate_daily_compact_report(client, cfg)
        chat_id = str(update.effective_chat.id)
        if chart is not None:
            dd_cfg = cfg.get("daily_dynamics") or {}
            phrase = dd_cfg.get("phrase", "тс пиот")
            caption = f"📊 Динамика за 30 дней — {phrase}"
            await send_telegram_photo(context.bot.token, chat_id, chart, caption=caption)
        await send_telegram(context.bot.token, chat_id, report)
        print("[OK] /dynamics sent")
    except Exception as exc:
        print(f"[ERROR] /dynamics: {exc}", file=sys.stderr)
        await update.message.reply_text(f"❌ Ошибка: {escape_html(str(exc))}")


async def _scheduled_wordstat_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduled job — send Wordstat digest to the configured chat."""
    client = context.bot_data.get("wordstat_client")
    cfg = context.bot_data.get("config")
    chat_id = context.bot_data.get("chat_id")
    if not client or not cfg or not chat_id:
        return
    try:
        print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Sending scheduled Wordstat report…")
        await send_telegram(context.bot.token, chat_id, await generate_report(client, cfg))
        print("Done ✓")
    except Exception as exc:
        print(f"ERROR in scheduled Wordstat report: {exc}", file=sys.stderr)


async def _scheduled_daily_dynamics(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduled job — send compact daily digest (top queries + daily dynamics)."""
    client = context.bot_data.get("wordstat_client")
    cfg = context.bot_data.get("config")
    chat_id = context.bot_data.get("chat_id")
    if not client or not cfg or not chat_id:
        return
    try:
        print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Sending daily compact report…")
        report, chart = await generate_daily_compact_report(client, cfg)
        if chart is not None:
            dd_cfg = cfg.get("daily_dynamics") or {}
            phrase = dd_cfg.get("phrase", "тс пиот")
            caption = f"📊 Динамика за 30 дней — {phrase}"
            await send_telegram_photo(context.bot.token, chat_id, chart, caption=caption)
        await send_telegram(context.bot.token, chat_id, report)
        print("Done ✓")
    except Exception as exc:
        print(f"ERROR in scheduled daily compact report: {exc}", file=sys.stderr)


def setup_wordstat_feature(app: Application, client: WordstatClient, cfg: dict) -> None:
    """Register all Wordstat handlers, the weekly scheduled digest, and daily dynamics."""
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("dynamics", dynamics_command))

    # Weekly Wordstat digest (Thursday by default)
    sched = cfg.get("schedule", {})
    weekday = int(sched.get("weekday", 3))
    hour = int(sched.get("hour", 4))
    minute = int(sched.get("minute", 20))
    app.job_queue.run_daily(
        _scheduled_wordstat_report,
        time=datetime.min.replace(hour=hour, minute=minute).time(),
        days=(weekday,),
        name="wordstat_digest",
    )
    print(f"[Wordstat] Scheduled digest: weekday={weekday} at {hour:02d}:{minute:02d} UTC")

    # Daily dynamics report
    dd_cfg = cfg.get("daily_dynamics", {})
    if dd_cfg:
        dd_sched = dd_cfg.get("schedule", {})
        dd_hour = int(dd_sched.get("hour", 4))
        dd_minute = int(dd_sched.get("minute", 30))
        app.job_queue.run_daily(
            _scheduled_daily_dynamics,
            time=datetime.min.replace(hour=dd_hour, minute=dd_minute).time(),
            name="daily_dynamics_digest",
        )
        print(f"[DailyDynamics] Scheduled daily at {dd_hour:02d}:{dd_minute:02d} UTC")


# ---------------------------------------------------------------------------
# Feature 2 — Telegram channel monitoring
# ---------------------------------------------------------------------------

async def _collect_channel_mentions(monitor, cfg: dict) -> tuple:
    """Returns (results, errors)."""
    chan_cfg = cfg.get("channel_monitor", {})
    channels = chan_cfg.get("channels", [])
    keywords = chan_cfg.get("keywords", [])
    hours_lookback = chan_cfg.get("hours_lookback", 36)

    if not channels or not keywords:
        return [], []

    print(f"[Monitor:TG] Начинаю проверку {len(channels)} каналов (окно: {hours_lookback}ч)")
    results = []
    errors = []
    for ch in channels:
        channel_name = ch.get("name", "Unknown")
        username = ch.get("username", "")
        channel_identifier = username or ch.get("channel_id")
        if not channel_identifier:
            print(f"[Monitor:TG] ⚠️  {channel_name} — нет идентификатора, пропускаю")
            errors.append(f"{channel_name} — нет идентификатора")
            continue
        try:
            print(f"[Monitor:TG] Проверяю {channel_name} ({channel_identifier})…", flush=True)
            messages = await monitor.get_messages_from_channel(channel_identifier, limit=100)
            fetched = len(messages) if messages else 0
            if not messages:
                print(f"[Monitor:TG] {channel_name}: 0 сообщений")
                continue
            matches = []
            for msg, keyword in MessageFilter.filter_messages(messages, keywords, hours_lookback):
                matches.append((parse_message_data(msg, channel_name, username), keyword))
            results.extend(matches)
            print(f"[Monitor:TG] {channel_name}: {fetched} сообщений, совпадений: {len(matches)}")
        except Exception as exc:
            msg = str(exc)
            print(f"[Monitor:TG] ❌ {channel_name}: {msg}", file=sys.stderr)
            errors.append(f"{channel_name} ({username}): {msg[:120]}")

    print(f"[Monitor:TG] Готово. Итого совпадений из TG: {len(results)}")
    return results, errors


async def _collect_rss_feed_mentions(cfg: dict) -> tuple:
    """Fetch all configured RSS feeds and filter by channel_monitor keywords.
    Returns (results, errors).
    """
    rss_cfg = cfg.get("rss_feeds", {})
    if not rss_cfg.get("enabled"):
        return [], []

    feeds = rss_cfg.get("feeds", [])
    if not feeds:
        return [], []

    # Re-use the same keywords and hours_lookback as channel monitoring
    keywords = cfg.get("channel_monitor", {}).get("keywords", [])
    hours_lookback = cfg.get("channel_monitor", {}).get("hours_lookback", 36)
    if not keywords:
        return [], []

    print(f"[Monitor:RSS] Начинаю проверку {len(feeds)} лент (окно: {hours_lookback}ч)")
    monitor = RSSFeedMonitor()
    results = []
    errors = []
    try:
        await monitor.connect()
        for feed in feeds:
            name = feed.get("name", "RSS")
            url = feed.get("url", "")
            if not url:
                print(f"[Monitor:RSS] ⚠️  {name} — нет URL, пропускаю")
                errors.append(f"RSS {name} — нет URL")
                continue
            try:
                print(f"[Monitor:RSS] Проверяю {name}…", flush=True)
                messages = await monitor.get_messages(name, url)
                fetched = len(messages) if messages else 0
                if not messages:
                    print(f"[Monitor:RSS] {name}: 0 сообщений")
                    continue
                matches = []
                for msg, keyword in MessageFilter.filter_messages(messages, keywords, hours_lookback):
                    matches.append((parse_message_data(msg, name, url), keyword))
                results.extend(matches)
                print(f"[Monitor:RSS] {name}: {fetched} сообщений, совпадений: {len(matches)}")
            except Exception as exc:
                msg = str(exc)
                print(f"[Monitor:RSS] ❌ {name}: {msg}", file=sys.stderr)
                errors.append(f"RSS {name}: {msg[:120]}")
    finally:
        await monitor.close()

    print(f"[Monitor:RSS] Готово. Итого совпадений из RSS: {len(results)}")
    return results, errors


async def _build_channel_summary(monitor, cfg: dict) -> str:
    hours_lookback = cfg.get("channel_monitor", {}).get("hours_lookback", 36)

    (channel_results, tg_errors), (rss_results, rss_errors) = await asyncio.gather(
        _collect_channel_mentions(monitor, cfg),
        _collect_rss_feed_mentions(cfg),
    )
    results = channel_results + rss_results
    all_errors = tg_errors + rss_errors
    print(f"[Monitor] Всего совпадений (TG + RSS): {len(results)}")

    parts = []
    if not results:
        parts.append(
            f"📊 <b>Мониторинг Telegram-каналов и RSS</b>\n\n"
            f"🔍 <i>Упоминания не найдены за последние {hours_lookback} часов</i>"
        )
    else:
        parts.extend(format_summary_with_pagination(group_results_by_keyword(results), hours_lookback))

    if all_errors:
        error_lines = ["⚠️ <b>Ошибки при проверке источников:</b>"]
        for e in all_errors:
            error_lines.append(f"  · {escape_html(e)}")
        parts.append("\n".join(error_lines))

    return "\n\n".join(parts)


async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /channels — scan channels for keywords and send summary on demand."""
    print(f"[COMMAND] /channels from user {update.effective_user.id}")
    monitor = context.bot_data.get("channel_monitor")
    cfg = context.bot_data.get("config")
    if not monitor or not cfg:
        await update.message.reply_text("❌ Мониторинг каналов не инициализирован.")
        return
    if not cfg.get("channel_monitor", {}).get("enabled"):
        await update.message.reply_text("❌ Мониторинг каналов отключен в конфиге.")
        return
    try:
        await update.message.reply_text("⏳ Анализирую каналы...")
        summary = await _build_channel_summary(monitor, cfg)
        for chunk in _split_message(summary):
            await send_telegram(context.bot.token, str(update.effective_chat.id), chunk)
        print("[OK] /channels sent")
    except Exception as exc:
        print(f"[ERROR] /channels: {exc}", file=sys.stderr)
        await update.message.reply_text(f"❌ Ошибка: {escape_html(str(exc))}")


async def _scheduled_channel_summary(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduled job — send channel monitoring digest to the configured chat."""
    monitor = context.bot_data.get("channel_monitor")
    cfg = context.bot_data.get("config")
    chat_id = context.bot_data.get("chat_id")
    if not monitor or not cfg or not chat_id:
        return
    if not cfg.get("channel_monitor", {}).get("enabled"):
        return
    try:
        print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Sending scheduled channel summary…")
        summary = await _build_channel_summary(monitor, cfg)
        for chunk in _split_message(summary):
            await send_telegram(context.bot.token, chat_id, chunk)
        print("Done ✓")
    except Exception as exc:
        print(f"ERROR in scheduled channel summary: {exc}", file=sys.stderr)


def setup_channel_feature(app: Application, monitor, cfg: dict) -> None:
    """Register all channel monitoring handlers and the daily scheduled digest."""
    app.add_handler(CommandHandler("channels", channels_command))

    chan_cfg = cfg.get("channel_monitor", {})
    chan_sched = chan_cfg.get("schedule", {})
    hour = int(chan_sched.get("hour", 4))
    minute = int(chan_sched.get("minute", 0))
    app.job_queue.run_daily(
        _scheduled_channel_summary,
        time=datetime.min.replace(hour=hour, minute=minute).time(),
        name="channel_digest",
    )
    print(f"[Channels] Scheduled digest: daily at {hour:02d}:{minute:02d} UTC")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /today — send daily dynamics + channel mentions together."""
    print(f"[COMMAND] /today from user {update.effective_user.id}")
    client: WordstatClient = context.bot_data.get("wordstat_client")
    monitor = context.bot_data.get("channel_monitor")
    cfg: dict = context.bot_data.get("config")
    if not client or not cfg:
        await update.message.reply_text("❌ Бот не инициализирован. Попробуйте позже.")
        return
    await update.message.reply_text("⏳ Собираю сводку за сегодня...")

    tasks: list = [generate_daily_compact_report(client, cfg)]
    if monitor and cfg.get("channel_monitor", {}).get("enabled"):
        tasks.append(_build_channel_summary(monitor, cfg))
    results = await asyncio.gather(*tasks, return_exceptions=True)

    chat_id = str(update.effective_chat.id)
    dd_cfg = cfg.get("daily_dynamics") or {}
    phrase = dd_cfg.get("phrase", "тс пиот")

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"[ERROR] /today partial: {result}", file=sys.stderr)
            await update.message.reply_text(f"❌ Ошибка: {escape_html(str(result))}")
        elif i == 0:
            # First result is (report, chart) from generate_daily_compact_report
            report, chart = result
            if chart is not None:
                await send_telegram_photo(
                    context.bot.token, chat_id, chart,
                    caption=f"📊 Динамика за 30 дней — {phrase}",
                )
            await send_telegram(context.bot.token, chat_id, report)
        else:
            # Channel summary is plain text
            for chunk in _split_message(result):
                await send_telegram(context.bot.token, chat_id, chunk)
    print("[OK] /today sent")


# ---------------------------------------------------------------------------
# General commands
# ---------------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет! Я — Wordstat + мониторинг каналов бот.\n\n"
        "/today — сводка за сегодня (поиск + СМИ)\n"
        "/dynamics — ежедневная сводка Wordstat\n"
        "/channels — упоминания в СМИ\n"
        "/report — полный Wordstat-отчёт\n"
        "/info — что делает этот бот\n"
        "/help — справка"
    )


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg: dict = context.bot_data.get("config") or {}

    lines = [
        "ℹ️ <b>О боте</b>",
        "",
        "Бот следит за тем, как люди ищут ТС ПИОТ в интернете и что пишут о нём в медиа.",
        "",
    ]

    # --- Wordstat: поисковые запросы ---
    analytics = cfg.get("analytics", [])
    dd_phrase = (cfg.get("daily_dynamics") or {}).get("phrase", "")
    if analytics or dd_phrase:
        lines.append("🔍 <b>Wordstat — отслеживаемые запросы</b>")
        if dd_phrase:
            lines.append(f"  Ежедневная динамика: <i>{escape_html(dd_phrase)}</i>")
        for group in analytics:
            gname = group.get("name", "")
            phrases = group.get("phrases", [])
            if phrases:
                lines.append(f"\n  <b>{escape_html(gname)}</b>:")
                for p in phrases:
                    lines.append(f"    · {escape_html(p)}")
        lines.append("")

    # --- Telegram-каналы ---
    chan_cfg = cfg.get("channel_monitor", {})
    channels = chan_cfg.get("channels", [])
    if channels:
        lines.append("📢 <b>Telegram-каналы</b>")
        for ch in channels:
            name = ch.get("name", "")
            username = ch.get("username", "")
            lines.append(f"  · {escape_html(name)} {escape_html(username)}")
        lines.append("")

    # --- RSS-ленты ---
    rss_cfg = cfg.get("rss_feeds", {})
    feeds = rss_cfg.get("feeds", []) if rss_cfg.get("enabled") else []
    if feeds:
        lines.append("📡 <b>RSS-ленты</b>")
        for feed in feeds:
            lines.append(f"  · {escape_html(feed.get('name', ''))}")
        lines.append("")

    # --- Ключевые слова мониторинга ---
    keywords = chan_cfg.get("keywords", [])
    if keywords:
        kw_str = ", ".join(f"«{escape_html(k)}»" for k in keywords)
        lines.append(f"🔑 <b>Ключевые слова в медиа:</b> {kw_str}")
        hours = chan_cfg.get("hours_lookback", 36)
        lines.append(f"  Окно поиска: последние {hours} часов")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 <b>Доступные команды:</b>\n\n"
        "/today — сводка за сегодня: поисковая динамика + упоминания в СМИ\n"
        "/dynamics — ежедневная сводка Wordstat (топ запросов + динамика)\n"
        "/channels — упоминания в Telegram-каналах и RSS\n"
        "/report — полный еженедельный Wordstat-отчёт\n"
        "/info — что делает этот бот\n"
        "/start — приветствие\n"
        "/help — эта справка",
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Launcher
# ---------------------------------------------------------------------------

async def main() -> None:
    parser = argparse.ArgumentParser(description="Wordstat + Channel monitor bot")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print Wordstat report to stdout and exit")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    wc_cfg = cfg.get("wordstat", {})
    tg_cfg = cfg.get("telegram", {})

    api_key = os.environ.get("YC_API_KEY") or wc_cfg.get("api_key", "")
    folder_id = os.environ.get("YC_FOLDER_ID") or wc_cfg.get("folder_id", "")
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or tg_cfg.get("bot_token", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or str(tg_cfg.get("chat_id", ""))

    if not api_key:
        print("ERROR: YC_API_KEY not set (Yandex Cloud API key for Search API).", file=sys.stderr)
        sys.exit(1)
    if not folder_id:
        print("ERROR: YC_FOLDER_ID not set (Yandex Cloud folder id).", file=sys.stderr)
        sys.exit(1)
    if not args.dry_run and not bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set.", file=sys.stderr)
        sys.exit(1)
    if not cfg.get("clusters"):
        print("ERROR: No clusters defined in config.", file=sys.stderr)
        sys.exit(1)

    # Diagnostic: confirm WHAT the bot actually reads from the environment.
    # The API key is never printed in full — only its length and a short tail —
    # so we can compare against the value tested with curl without leaking it.
    print(
        f"[WORDSTAT] folder_id={folder_id!r} "
        f"api_key_len={len(api_key)} api_key_tail=…{api_key[-4:] if len(api_key) >= 4 else ''} "
        f"base_url={wc_cfg.get('base_url', 'https://searchapi.api.cloud.yandex.net/v2/wordstat')}",
        file=sys.stderr,
    )

    client = WordstatClient(
        api_key=api_key,
        folder_id=folder_id,
        base_url=wc_cfg.get("base_url", "https://searchapi.api.cloud.yandex.net/v2/wordstat"),
    )

    # Dry-run: just print the report and exit
    if args.dry_run:
        print("\n" + "=" * 60)
        print(await generate_report(client, cfg))
        return

    # --- Build the bot application ---
    print(f"Starting bot… chat_id={chat_id!r}")
    app = Application.builder().token(bot_token).build()
    app.bot_data.update({"wordstat_client": client, "config": cfg, "chat_id": chat_id})

    # General commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("help", help_command))

    # Feature 1: Wordstat
    setup_wordstat_feature(app, client, cfg)

    # Feature 2: channel monitoring
    chan_cfg = cfg.get("channel_monitor", {})
    channel_monitor = None
    if chan_cfg.get("enabled"):
        print("Initializing channel monitor…")
        try:
            channel_monitor = await create_monitor()
            if channel_monitor:
                kind = "Telethon" if "RSS" not in type(channel_monitor).__name__ else "RSS"
                print(f"✓ Channel monitor ready ({kind})")
            else:
                print("⚠️  Channel monitor failed to initialize")
        except Exception as exc:
            print(f"❌ Channel monitor error: {exc}", file=sys.stderr)

    app.bot_data["channel_monitor"] = channel_monitor
    if channel_monitor:
        setup_channel_feature(app, channel_monitor, cfg)

    # --- Start polling ---
    print("Bot is listening for commands…")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=["message", "channel_post"])

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\nShutting down…")
    finally:
        if channel_monitor:
            await channel_monitor.close()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
