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

from wordstat import WordstatClient, generate_report, escape_html
from telegram_channel_monitor.channel_monitor import create_monitor
from telegram_channel_monitor.message_filter import MessageFilter
from telegram_channel_monitor.message_parser import parse_message_data
from telegram_channel_monitor.summary_formatter import (
    group_results_by_keyword,
    format_summary_with_pagination,
)


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


def setup_wordstat_feature(app: Application, client: WordstatClient, cfg: dict) -> None:
    """Register all Wordstat handlers and the weekly scheduled digest."""
    app.add_handler(CommandHandler("report", report_command))

    sched = cfg.get("schedule", {})
    weekday = int(sched.get("weekday", 0))
    hour = int(sched.get("hour", 7))
    minute = int(sched.get("minute", 0))
    app.job_queue.run_daily(
        _scheduled_wordstat_report,
        time=datetime.min.replace(hour=hour, minute=minute).time(),
        days=(weekday,),
        name="wordstat_digest",
    )
    print(f"[Wordstat] Scheduled digest: weekday={weekday} at {hour:02d}:{minute:02d} UTC")


# ---------------------------------------------------------------------------
# Feature 2 — Telegram channel monitoring
# ---------------------------------------------------------------------------

async def _collect_channel_mentions(monitor, cfg: dict) -> list:
    chan_cfg = cfg.get("channel_monitor", {})
    channels = chan_cfg.get("channels", [])
    keywords = chan_cfg.get("keywords", [])
    hours_lookback = chan_cfg.get("hours_lookback", 36)

    if not channels or not keywords:
        return []

    results = []
    for ch in channels:
        channel_name = ch.get("name", "Unknown")
        username = ch.get("username", "")
        channel_identifier = username or ch.get("channel_id")
        if not channel_identifier:
            continue
        try:
            messages = await monitor.get_messages_from_channel(channel_identifier, limit=100)
            if not messages:
                continue
            for msg, keyword in MessageFilter.filter_messages(messages, keywords, hours_lookback):
                results.append((parse_message_data(msg, channel_name, username), keyword))
        except Exception as exc:
            print(f"⚠️  Error processing {channel_name}: {exc}", file=sys.stderr)

    return results


async def _build_channel_summary(monitor, cfg: dict) -> str:
    hours_lookback = cfg.get("channel_monitor", {}).get("hours_lookback", 36)
    results = await _collect_channel_mentions(monitor, cfg)
    if not results:
        return (
            f"📊 <b>Мониторинг Telegram-каналов</b>\n\n"
            f"🔍 <i>Упоминания не найдены за последние {hours_lookback} часов</i>"
        )
    return "\n\n".join(
        format_summary_with_pagination(group_results_by_keyword(results), hours_lookback)
    )


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
    weekday = int(chan_sched.get("weekday", 1))
    hour = int(chan_sched.get("hour", 10))
    minute = int(chan_sched.get("minute", 0))
    app.job_queue.run_daily(
        _scheduled_channel_summary,
        time=datetime.min.replace(hour=hour, minute=minute).time(),
        days=(weekday,),
        name="channel_digest",
    )
    print(f"[Channels] Scheduled digest: weekday={weekday} at {hour:02d}:{minute:02d} UTC")


# ---------------------------------------------------------------------------
# General commands
# ---------------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет! Я — Wordstat + мониторинг каналов бот.\n\n"
        "/report — отчёт из Wordstat\n"
        "/channels — упоминания в Telegram-каналах\n"
        "/help — справка"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 <b>Доступные команды:</b>\n\n"
        "/report — получить Wordstat-отчёт сейчас\n"
        "/channels — мониторинг Telegram-каналов сейчас\n"
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

    oauth_token = os.environ.get("WORDSTAT_OAUTH_TOKEN") or wc_cfg.get("oauth_token", "")
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or tg_cfg.get("bot_token", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or str(tg_cfg.get("chat_id", ""))

    if not oauth_token:
        print("ERROR: WORDSTAT_OAUTH_TOKEN not set.", file=sys.stderr)
        sys.exit(1)
    if not args.dry_run and not bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set.", file=sys.stderr)
        sys.exit(1)
    if not cfg.get("clusters"):
        print("ERROR: No clusters defined in config.", file=sys.stderr)
        sys.exit(1)

    client = WordstatClient(
        oauth_token=oauth_token,
        base_url=wc_cfg.get("base_url", "https://api.wordstat.yandex.net"),
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
