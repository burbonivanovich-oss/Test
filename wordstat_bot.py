#!/usr/bin/env python3
"""
Wordstat → Telegram Bot
Collects data from Yandex Wordstat API across query clusters and sends a digest to Telegram.

Usage:
    python wordstat_bot.py [--config config.yaml]
"""

import argparse
import sys
import textwrap
from datetime import date, timedelta

import requests
import yaml


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
    lines = [f"🔍 *{phrase}* — топ запросов (30 дней)"]
    if not items:
        lines.append("  _нет данных_")
        return lines
    for i, item in enumerate(items[:top_n], 1):
        count = _fmt_number(item.get("count", 0))
        kw = item.get("phrase", "—")
        lines.append(f"  {i}\\. {kw} — {count}")
    return lines


def format_dynamics(phrase: str, items: list[dict]) -> list[str]:
    lines = [f"📈 *{phrase}* — динамика"]
    if not items:
        lines.append("  _нет данных_")
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
    lines = [f"🗺 *{phrase}* — топ регионов (30 дней)"]
    if not items:
        lines.append("  _нет данных_")
        return lines
    sorted_items = sorted(items, key=lambda x: x.get("count", 0), reverse=True)
    for item in sorted_items[:top_n]:
        count = _fmt_number(item.get("count", 0))
        rid = item.get("regionId", "?")
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

    section: list[str] = [f"*━━ {name} ━━*"]

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
                section.append(f"  ⚠️ Неизвестный метод: {method}")

        except requests.HTTPError as exc:
            section.append(f"  ❌ Ошибка API для «{phrase}»: {exc.response.status_code}")
        except Exception as exc:  # noqa: BLE001
            section.append(f"  ❌ Ошибка для «{phrase}»: {exc}")

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
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True,
        }, timeout=30)
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


def escape_md(text: str) -> str:
    """Escape special chars for Telegram MarkdownV2 (outside bold/italic markers)."""
    special = r"\_[]()~`>#+-=|{}.!"
    for ch in special:
        text = text.replace(ch, f"\\{ch}")
    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_report(clusters_data: list[list[str]]) -> str:
    today = date.today().strftime("%d.%m.%Y")
    header = [f"📊 *Wordstat дайджест* — {escape_md(today)}", ""]
    lines: list[str] = header
    for section in clusters_data:
        lines += section
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Wordstat → Telegram digest")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print report to stdout, don't send to Telegram")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    wc_cfg = cfg["wordstat"]
    tg_cfg = cfg["telegram"]
    clusters = cfg.get("clusters", [])

    if not clusters:
        print("No clusters defined in config. Exiting.", file=sys.stderr)
        sys.exit(1)

    client = WordstatClient(
        oauth_token=wc_cfg["oauth_token"],
        base_url=wc_cfg.get("base_url", "https://api.wordstat.yandex.net"),
    )

    print(f"Processing {len(clusters)} cluster(s)…")
    sections: list[list[str]] = []
    for cluster in clusters:
        print(f"  → {cluster.get('name', '?')}")
        sections.append(process_cluster(client, cluster))

    report = build_report(sections)

    if args.dry_run:
        print("\n" + "=" * 60)
        # Print plain version (strip escape backslashes for readability)
        print(report.replace("\\", ""))
        return

    print("Sending to Telegram…")
    send_telegram(tg_cfg["bot_token"], str(tg_cfg["chat_id"]), report)
    print("Done ✓")


if __name__ == "__main__":
    main()
