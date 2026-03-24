"""
Wordstat API client and report builder.

Pure business logic — no Telegram code here.
Imported by main.py to power the /report command and scheduled digests.
"""

import asyncio
from datetime import date, timedelta

import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def escape_html(text: str) -> str:
    """Escape special chars for Telegram HTML mode."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt_number(n: int | float) -> str:
    return f"{int(n):,}".replace(",", "\u202f")  # narrow no-break space as thousands sep


def _default_from_date(period: str) -> str:
    today = date.today()
    if period == "monthly":
        first_this = today.replace(day=1)
        last_month = first_this - timedelta(days=1)
        return last_month.replace(day=1).isoformat()
    if period == "weekly":
        monday = today - timedelta(days=today.weekday())
        return (monday - timedelta(weeks=4)).isoformat()
    return (today - timedelta(days=30)).isoformat()


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
        return self._post("/v1/topRequests", payload).get("topRequests", [])

    def dynamics(self, phrase: str, period: str, from_date: str, to_date: str = None,
                 regions: list[int] = None, devices: list[str] = None) -> list[dict]:
        payload: dict = {"phrase": self._fmt_phrase(phrase), "period": period, "fromDate": from_date}
        if to_date:
            payload["toDate"] = to_date
        if regions:
            payload["regions"] = regions
        if devices and devices != ["all"]:
            payload["devices"] = devices
        return self._post("/v1/dynamics", payload).get("dynamics", [])

    def regions(self, phrase: str, region_type: str = "all",
                devices: list[str] = None) -> list[dict]:
        payload: dict = {"phrase": self._fmt_phrase(phrase), "regionType": region_type}
        if devices and devices != ["all"]:
            payload["devices"] = devices
        return self._post("/v1/regions", payload).get("regions", [])


# ---------------------------------------------------------------------------
# Report formatters
# ---------------------------------------------------------------------------

def format_top_requests(phrase: str, items: list[dict], top_n: int = 10) -> list[str]:
    lines = [f"🔍 <b>{escape_html(phrase)}</b> — топ запросов (30 дней)"]
    if not items:
        lines.append("  <i>нет данных</i>")
        return lines
    for i, item in enumerate(items[:top_n], 1):
        lines.append(f"  {i}. {escape_html(item.get('phrase', '—'))} — {_fmt_number(item.get('count', 0))}")
    return lines


def format_dynamics(phrase: str, items: list[dict]) -> list[str]:
    lines = [f"📈 <b>{escape_html(phrase)}</b> — динамика"]
    if not items:
        lines.append("  <i>нет данных</i>")
        return lines
    for item in items[-6:]:
        lines.append(f"  {item.get('date', '?')}: {_fmt_number(item.get('count', 0))} ({item.get('share', 0):.4f}%)")
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
    for item in sorted(items, key=lambda x: x.get("count", 0), reverse=True)[:top_n]:
        lines.append(
            f"  [{escape_html(str(item.get('regionId', '?')))}] "
            f"{_fmt_number(item.get('count', 0))} запросов, affinity {item.get('affinityIndex', 0)}%"
        )
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
                section += format_top_requests(phrase, client.top_requests(phrase, regions=regions, devices=devices))
            elif method == "dynamics":
                period = cluster.get("period", "monthly")
                section += format_dynamics(phrase, client.dynamics(
                    phrase, period=period,
                    from_date=cluster.get("from_date") or _default_from_date(period),
                    to_date=cluster.get("to_date"), regions=regions, devices=devices,
                ))
            elif method == "regions":
                section += format_regions(phrase, client.regions(
                    phrase, region_type=cluster.get("region_type", "all"), devices=devices,
                ))
            else:
                section.append(f"  ⚠️ Неизвестный метод: {escape_html(method)}")
        except requests.HTTPError as exc:
            section.append(f"  ❌ Ошибка API для «{escape_html(phrase)}»: {escape_html(str(exc))}")
        except Exception as exc:  # noqa: BLE001
            section.append(f"  ❌ Ошибка для «{escape_html(phrase)}»: {escape_html(str(exc))}")

    return section


# ---------------------------------------------------------------------------
# Weekly analytics summary
# ---------------------------------------------------------------------------

def build_analytics_summary(client: WordstatClient, analytics: list[dict],
                             data_ready_weekday: int = 3) -> list[str]:
    """Build weekly analytics summary comparing current week vs previous week."""
    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    prev_sunday = last_sunday - timedelta(weeks=1)

    if today.weekday() < data_ready_weekday:
        last_sunday -= timedelta(weeks=1)
        prev_sunday -= timedelta(weeks=1)

    week_monday = last_sunday - timedelta(days=6)
    week_label = f"{week_monday.strftime('%d.%m.%Y')} \u2013 {last_sunday.strftime('%d.%m.%Y')}"
    from_date = (prev_sunday - timedelta(days=6)).isoformat()
    to_date = last_sunday.isoformat()

    lines: list[str] = [f"📋 <b>Сводка за неделю {escape_html(week_label)}</b>", ""]

    for group in analytics:
        name = group.get("name", "Группа")
        phrases = group.get("phrases", [])
        regions = group.get("regions") or []
        devices = group.get("devices", ["all"])
        current_total = prev_total = 0
        errors: list[str] = []

        for phrase in phrases:
            try:
                items = client.dynamics(phrase, period="weekly", from_date=from_date,
                                        to_date=to_date, regions=regions, devices=devices)
                if len(items) >= 2:
                    prev_total += items[-2].get("count", 0)
                    current_total += items[-1].get("count", 0)
            except requests.HTTPError as exc:
                errors.append(f"  ❌ Ошибка API для «{escape_html(phrase)}»: {escape_html(str(exc))}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"  ❌ Ошибка для «{escape_html(phrase)}»: {escape_html(str(exc))}")

        delta = current_total - prev_total
        if prev_total:
            pct = delta / prev_total * 100
            sign = "+" if delta >= 0 else ""
            change_str = f"{sign}{delta:,} ({sign}{pct:.1f}%)".replace(",", "\u202f")
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
# Report assembly
# ---------------------------------------------------------------------------

def build_report(clusters_data: list[list[str]],
                 summary_lines: list[str] | None = None) -> str:
    today = date.today().strftime("%d.%m.%Y")
    lines: list[str] = [f"📊 <b>Wordstat дайджест</b> — {escape_html(today)}", ""]
    if summary_lines:
        lines += summary_lines
        lines.append("")
    for section in clusters_data:
        lines += section
        lines.append("")
    return "\n".join(lines)


def _sync_generate_report(client: WordstatClient, cfg: dict) -> str:
    """Synchronous entry point — all blocking Wordstat HTTP calls happen here."""
    clusters = cfg.get("clusters", [])
    analytics = cfg.get("analytics", [])
    wc_cfg = cfg.get("wordstat", {})

    summary_lines: list[str] = []
    if analytics:
        summary_lines = build_analytics_summary(
            client, analytics, int(wc_cfg.get("data_ready_weekday", 3))
        )

    return build_report(
        [process_cluster(client, c) for c in clusters],
        summary_lines,
    )


async def generate_report(client: WordstatClient, cfg: dict) -> str:
    """Async wrapper — offloads blocking HTTP calls to a thread-pool executor."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_generate_report, client, cfg)
