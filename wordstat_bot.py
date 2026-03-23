#!/usr/bin/env python3
"""
Wordstat → Telegram Bot
Collects data from Yandex Wordstat API across query clusters and sends a digest to Telegram.

Usage:
    python wordstat_bot.py [--config config.yaml]
"""

import argparse
import os
import sys
import textwrap
import time
from datetime import date, datetime, timedelta

import requests
import yaml

# Load .env file if present (local dev); silently skip if python-dotenv not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


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
        resp.raise_for_status()
        return resp.json()

    def get_regions_tree(self) -> dict:
        return self._post("/v1/getRegionsTree", {})

    def top_requests(self, phrase: str, regions: list[int] = None,
                     devices: list[str] = None) -> list[dict]:
        payload: dict = {"phrase": phrase}
        if regions:
            payload["regions"] = regions
        if devices and devices != ["all"]:
            payload["devices"] = devices
        data = self._post("/v1/topRequests", payload)
        return data.get("topRequests", [])

    def dynamics(self, phrase: str, period: str, from_date: str, to_date: str = None,
                 regions: list[int] = None, devices: list[str] = None) -> list[dict]:
        payload: dict = {"phrase": phrase, "period": period, "fromDate": from_date}
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
        payload: dict = {"phrase": phrase, "regionType": region_type}
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
            section.append(f"  ❌ Ошибка API для «{escape_html(phrase)}»: {exc.response.status_code}")
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

def build_analytics_summary(client: WordstatClient, analytics: list[dict]) -> list[str]:
    """Build weekly analytics summary comparing current week vs previous week.

    The Wordstat API requires toDate for period=weekly to be a Sunday.
    We use the most recently completed Sunday as 'current week' and the
    Sunday before that as 'previous week'.
    """
    today = date.today()
    # Most recently completed Sunday: Mon=0 → 1 day back, Sun=6 → 0 days back
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    prev_sunday = last_sunday - timedelta(weeks=1)

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
            except Exception:  # noqa: BLE001
                pass

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
            "",
        ]

    return lines


# ---------------------------------------------------------------------------
# Telegram sender
# ---------------------------------------------------------------------------

def send_telegram(bot_token: str, chat_id: str, text: str) -> None:
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
# Main
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


def _next_run_utc(weekday: int, hour: int, minute: int) -> datetime:
    """Return next UTC datetime matching the given weekday/hour/minute."""
    now = datetime.utcnow()
    days_ahead = (weekday - now.weekday()) % 7
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if days_ahead == 0 and now >= candidate:
        days_ahead = 7
    return candidate + timedelta(days=days_ahead)


def run_once(client: WordstatClient, cfg: dict, bot_token: str, chat_id: str,
             dry_run: bool) -> None:
    clusters = cfg.get("clusters", [])
    analytics = cfg.get("analytics", [])

    summary_lines: list[str] = []
    if analytics:
        print(f"Building analytics summary ({len(analytics)} group(s))…")
        summary_lines = build_analytics_summary(client, analytics)

    print(f"Processing {len(clusters)} cluster(s)…")
    sections: list[list[str]] = []
    for cluster in clusters:
        print(f"  → {cluster.get('name', '?')}")
        sections.append(process_cluster(client, cluster))

    report = build_report(sections, summary_lines)

    if dry_run:
        print("\n" + "=" * 60)
        print(report.replace("\\", ""))
        return

    print("Sending to Telegram…")
    send_telegram(bot_token, chat_id, report)
    print("Done ✓")


def main() -> None:
    parser = argparse.ArgumentParser(description="Wordstat → Telegram digest")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print report to stdout, don't send to Telegram")
    parser.add_argument("--daemon", action="store_true",
                        help="Run on schedule (for bothost.ru / long-running process)")
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

    if not args.daemon:
        run_once(client, cfg, bot_token, chat_id, args.dry_run)
        return

    # Daemon mode: sleep until scheduled time, then run, repeat
    sched = cfg.get("schedule", {})
    weekday = int(sched.get("weekday", 0))   # 0=Monday … 6=Sunday
    hour = int(sched.get("hour", 7))
    minute = int(sched.get("minute", 0))

    print(f"Daemon mode: will run every weekday={weekday} at {hour:02d}:{minute:02d} UTC")
    while True:
        next_run = _next_run_utc(weekday, hour, minute)
        wait_secs = (next_run - datetime.utcnow()).total_seconds()
        print(f"Next run: {next_run.strftime('%Y-%m-%d %H:%M')} UTC "
              f"(in {wait_secs / 3600:.1f}h)")
        time.sleep(wait_secs)
        try:
            run_once(client, cfg, bot_token, chat_id, args.dry_run)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR during run: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
