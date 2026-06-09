"""
Wordstat API client and report builder.

Pure business logic — no Telegram code here.
Imported by main.py to power the /report command and scheduled digests.
"""

import asyncio
import os
import sys
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

        # Emergency override: Yandex sometimes serves a cert whose CN doesn't
        # match api.wordstat.yandex.net. When that happens, set this env var
        # to keep the bot running until they fix it. Default is strict TLS.
        if os.environ.get("WORDSTAT_INSECURE_TLS") == "1":
            self.session.verify = False
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            print(
                "⚠️  WORDSTAT_INSECURE_TLS=1 — TLS verification disabled for Wordstat",
                file=sys.stderr,
            )

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


def format_daily_dynamics(phrase: str, items: list[dict]) -> list[str]:
    """Format last 7 available days with date labels."""
    lines = [f"📅 <b>{escape_html(phrase)}</b> — динамика по дням"]
    if not items:
        lines.append("  <i>нет данных</i>")
        return lines
    last7 = items[-7:]
    for item in last7:
        raw_date = item.get("date", "?")
        try:
            d = date.fromisoformat(raw_date)
            label = d.strftime("%d.%m.%Y")
        except Exception:
            label = raw_date
        lines.append(f"  {label}: {_fmt_number(item.get('count', 0))}")
    if len(last7) >= 2:
        first_count = last7[0].get("count", 0)
        last_count = last7[-1].get("count", 0)
        if first_count:
            delta = (last_count - first_count) / first_count * 100
            arrow = "↑" if delta >= 0 else "↓"
            lines.append(f"  Тренд: {arrow} {abs(delta):.1f}% за период")
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

    # Daily dynamics section (last 7 days by day)
    daily_lines: list[str] = []
    dd_cfg = cfg.get("daily_dynamics", {})
    if dd_cfg:
        phrase = dd_cfg.get("phrase", "тс пиот")
        regions = dd_cfg.get("regions") or []
        devices = dd_cfg.get("devices", ["all"])
        today = date.today()
        try:
            items = client.dynamics(phrase, period="daily",
                                    from_date=(today - timedelta(days=8)).isoformat(),
                                    to_date=today.isoformat(),
                                    regions=regions, devices=devices)
            daily_lines = format_daily_dynamics(phrase, items)
        except Exception as exc:  # noqa: BLE001
            daily_lines = [f"❌ Ошибка динамики по дням: {escape_html(str(exc))}"]

    clusters_data = [process_cluster(client, c) for c in clusters]
    if daily_lines:
        clusters_data.append(daily_lines)

    return build_report(clusters_data, summary_lines)


async def generate_report(client: WordstatClient, cfg: dict) -> str:
    """Async wrapper — offloads blocking HTTP calls to a thread-pool executor."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_generate_report, client, cfg)


# ---------------------------------------------------------------------------
# Daily dynamics report
# ---------------------------------------------------------------------------

def _sync_generate_daily_dynamics_report(client: WordstatClient, phrase: str,
                                          regions: list[int] = None,
                                          devices: list[str] = None) -> str:
    today = date.today()
    from_date = (today - timedelta(days=8)).isoformat()
    to_date = today.isoformat()
    title_date = today.strftime("%d.%m.%Y")

    lines = [f"📈 <b>Динамика запросов по дням</b> — {escape_html(title_date)}", ""]
    try:
        items = client.dynamics(phrase, period="daily",
                                from_date=from_date, to_date=to_date,
                                regions=regions or [], devices=devices or ["all"])
        lines += format_daily_dynamics(phrase, items)
    except requests.HTTPError as exc:
        lines.append(f"❌ Ошибка API: {escape_html(str(exc))}")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"❌ Ошибка: {escape_html(str(exc))}")

    return "\n".join(lines)


async def generate_daily_dynamics_report(client: WordstatClient, phrase: str,
                                          regions: list[int] = None,
                                          devices: list[str] = None) -> str:
    """Async wrapper for daily dynamics report."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _sync_generate_daily_dynamics_report, client, phrase, regions, devices
    )


# ---------------------------------------------------------------------------
# Chart generation (requires matplotlib; gracefully degrades if missing)
# ---------------------------------------------------------------------------

try:
    import io as _io
    import matplotlib as _mpl
    _mpl.use("Agg")
    import matplotlib.pyplot as _plt
    import matplotlib.ticker as _mticker
    _HAS_MATPLOTLIB = True
except ImportError:
    _HAS_MATPLOTLIB = False


def _moving_avg(values: list[float], window: int = 7) -> list[float | None]:
    result: list[float | None] = []
    for i, _ in enumerate(values):
        if i < window - 1:
            result.append(None)
        else:
            result.append(sum(values[i - window + 1: i + 1]) / window)
    return result


def generate_daily_chart(phrase: str, items: list[dict]) -> "object | None":
    """Generate a 30-day bar chart as a PNG BytesIO. Returns None if matplotlib is absent."""
    if not _HAS_MATPLOTLIB or not items:
        return None
    try:
        last30 = items[-30:]
        dates: list[date] = []
        counts: list[float] = []
        for item in last30:
            try:
                dates.append(date.fromisoformat(item["date"]))
                counts.append(float(item.get("count", 0)))
            except Exception:
                continue
        if not dates:
            return None

        colors = ["#B0C4DE" if d.weekday() >= 5 else "#4A90D9" for d in dates]
        ma = _moving_avg(counts, window=7)

        fig, ax = _plt.subplots(figsize=(12, 4))
        ax.bar(range(len(dates)), counts, color=colors, alpha=0.85, width=0.8, zorder=2)

        # 7-day moving average line
        ma_x = [i for i, v in enumerate(ma) if v is not None]
        ma_y = [v for v in ma if v is not None]
        if ma_x:
            ax.plot(ma_x, ma_y, color="#E07B39", linewidth=1.8, zorder=5, label="MA 7 дней")

        # X-axis: labels every 5 bars
        ax.set_xticks(range(len(dates)))
        xlabels = [d.strftime("%d.%m") if i % 5 == 0 else "" for i, d in enumerate(dates)]
        ax.set_xticklabels(xlabels, rotation=45, ha="right", fontsize=8)

        # Faint Monday vertical lines to segment weeks
        for i, d in enumerate(dates):
            if d.weekday() == 0:
                ax.axvline(i, color="#AAAAAA", linewidth=0.5, linestyle="--", alpha=0.4, zorder=1)

        # Y-axis formatting
        ax.yaxis.set_major_formatter(_mticker.FuncFormatter(
            lambda x, _: f"{int(x):,}".replace(",", "\u202f")
        ))
        ax.set_ylim(bottom=0)
        ax.yaxis.grid(True, color="#EEEEEE", linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)

        # Spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Legend
        from matplotlib.patches import Patch as _Patch
        legend_elements = [
            _Patch(facecolor="#4A90D9", alpha=0.85, label="Рабочий день"),
            _Patch(facecolor="#B0C4DE", alpha=0.85, label="Выходной"),
        ]
        if ma_x:
            from matplotlib.lines import Line2D as _Line2D
            legend_elements.append(_Line2D([0], [0], color="#E07B39", linewidth=1.8, label="MA 7 дней"))
        ax.legend(handles=legend_elements, loc="upper left", framealpha=0.7, fontsize=8)

        # Title
        if len(dates) >= 2:
            title = (f"{phrase}  —  динамика по дням  "
                     f"({dates[0].strftime('%d.%m.%Y')} – {dates[-1].strftime('%d.%m.%Y')})")
        else:
            title = f"{phrase}  —  динамика по дням"
        ax.set_title(title, fontsize=11, fontweight="bold", pad=10)

        _plt.tight_layout(pad=1.2)
        buf = _io.BytesIO()
        fig.savefig(buf, format="png", dpi=100)
        _plt.close(fig)
        buf.seek(0)
        return buf
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Analytics helpers (WoW, profile, anomalies)
# ---------------------------------------------------------------------------

_DAY_NAMES_RU = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
_DATA_LAG = 3  # days: Wordstat shows data up to today - DATA_LAG


def _find_last_complete_workweek(today: date) -> tuple:
    """
    Returns (curr_mon, curr_fri, prev_mon, prev_fri) for the two most recent
    complete Mon-Fri working weeks where all 5 days have available data.
    Accounts for DATA_LAG.
    """
    last_available = today - timedelta(days=_DATA_LAG)
    days_since_friday = (last_available.weekday() - 4) % 7
    curr_fri = last_available - timedelta(days=days_since_friday)
    curr_mon = curr_fri - timedelta(days=4)
    prev_fri = curr_mon - timedelta(days=3)
    prev_mon = prev_fri - timedelta(days=4)
    return curr_mon, curr_fri, prev_mon, prev_fri


def format_wow_comparison(phrase: str, items: list[dict]) -> list[str]:
    """
    Week-over-week comparison of two complete Mon-Fri working weeks.
    Only meaningful on Mondays (caller is responsible for the guard).
    """
    if not items:
        return []

    today = date.today()
    curr_mon, curr_fri, prev_mon, prev_fri = _find_last_complete_workweek(today)

    by_date: dict[date, int] = {}
    for item in items:
        try:
            by_date[date.fromisoformat(item["date"])] = item.get("count", 0)
        except Exception:
            continue

    curr_days = [curr_mon + timedelta(days=i) for i in range(5)]
    prev_days = [prev_mon + timedelta(days=i) for i in range(5)]

    curr_counts = [by_date.get(d) for d in curr_days]
    prev_counts = [by_date.get(d) for d in prev_days]

    curr_valid = [c for c in curr_counts if c is not None]
    prev_valid = [c for c in prev_counts if c is not None]

    if not curr_valid or not prev_valid:
        return []

    curr_avg = sum(curr_valid) / len(curr_valid)
    prev_avg = sum(prev_valid) / len(prev_valid)

    if prev_avg:
        pct = (curr_avg - prev_avg) / prev_avg * 100
        arrow = "↑" if pct >= 0 else "↓"
        change = f"{arrow} {'+' if pct >= 0 else ''}{pct:.1f}%"
    else:
        change = "н/д"

    curr_label = f"{curr_mon.strftime('%d.%m')}–{curr_fri.strftime('%d.%m')}"
    prev_label = f"{prev_mon.strftime('%d.%m')}–{prev_fri.strftime('%d.%m')}"

    lines = [
        f"📅 <b>Неделя к неделе</b> — {escape_html(phrase)}",
        "",
        f"  Текущая ({curr_label}): ср/д {_fmt_number(curr_avg)} {change}",
        f"  Прошлая ({prev_label}): ср/д {_fmt_number(prev_avg)}",
        "",
    ]

    for i, (c_day, p_day) in enumerate(zip(curr_days, prev_days)):
        day_ru = _DAY_NAMES_RU[i]
        c_val = _fmt_number(curr_counts[i]) if curr_counts[i] is not None else "н/д"
        p_val = _fmt_number(prev_counts[i]) if prev_counts[i] is not None else "н/д"
        lines.append(
            f"  {day_ru}  {c_day.strftime('%d.%m')}  {c_val} | "
            f"{p_day.strftime('%d.%m')}  {p_val}"
        )

    return lines


def format_weekday_profile(items: list[dict]) -> list[str]:
    """Average daily count per weekday (Mon-Fri) across all available data."""
    from collections import defaultdict
    buckets: dict[int, list[int]] = defaultdict(list)
    for item in items:
        try:
            d = date.fromisoformat(item["date"])
            if d.weekday() < 5:  # Mon-Fri only
                buckets[d.weekday()].append(item.get("count", 0))
        except Exception:
            continue

    if not any(buckets.values()):
        return []

    parts = []
    for wd in range(5):
        vals = buckets.get(wd, [])
        avg = sum(vals) / len(vals) if vals else 0
        parts.append(f"{_DAY_NAMES_RU[wd]}: {_fmt_number(avg)}")

    return ["📆 <b>Профиль по дням недели</b>", "  " + "  ".join(parts)]


def format_anomalies(items: list[dict], threshold: float = 0.25) -> list[str]:
    """
    Compare each of the last 7 days against the 4-week same-weekday average.
    Flag days that deviate by more than threshold (default 25%).
    """
    from collections import defaultdict
    by_date: dict[date, int] = {}
    for item in items:
        try:
            by_date[date.fromisoformat(item["date"])] = item.get("count", 0)
        except Exception:
            continue

    if not by_date:
        return []

    sorted_dates = sorted(by_date)
    last7 = sorted_dates[-7:]

    # Build weekday baselines from days older than the last 7
    baseline_pool = sorted_dates[:-7]
    wd_baselines: dict[int, list[int]] = defaultdict(list)
    for d in baseline_pool:
        wd_baselines[d.weekday()].append(by_date[d])

    anomaly_lines = []
    for d in last7:
        count = by_date[d]
        wd = d.weekday()
        baseline = wd_baselines.get(wd, [])
        if not baseline:
            continue
        norm = sum(baseline) / len(baseline)
        if norm == 0:
            continue
        delta_pct = (count - norm) / norm
        if abs(delta_pct) >= threshold:
            sign = "+" if delta_pct >= 0 else ""
            anomaly_lines.append(
                f"  {d.strftime('%d.%m')} ({_DAY_NAMES_RU[wd]}): "
                f"{_fmt_number(count)} ⚡ {sign}{delta_pct * 100:.0f}% "
                f"vs норма {_fmt_number(norm)}"
            )

    if not anomaly_lines:
        return []

    return ["⚡ <b>Аномалии</b>"] + anomaly_lines


# ---------------------------------------------------------------------------
# Daily compact report (top queries + daily dynamics)
# ---------------------------------------------------------------------------

def _sync_generate_daily_compact_report(
    client: WordstatClient, cfg: dict
) -> "tuple[str, object | None]":
    """
    Compact daily digest: top queries + daily dynamics + analytics blocks.
    Returns (report_text, chart_BytesIO_or_None).
    Fetches 35 days so one API call feeds the 7-day table, WoW comparison, and 30-day chart.
    """
    today = date.today()
    title_date = today.strftime("%d.%m.%Y")
    lines: list[str] = [f"📊 <b>Wordstat дайджест</b> — {escape_html(title_date)}", ""]

    # Top requests — first cluster from config
    clusters = cfg.get("clusters", [])
    if clusters:
        lines += process_cluster(client, clusters[0])
        lines.append("")

    # Fetch 35 days of daily dynamics in one call
    dd_cfg = cfg.get("daily_dynamics") or {}
    phrase = dd_cfg.get("phrase", "тс пиот")
    regions = dd_cfg.get("regions") or []
    devices = dd_cfg.get("devices", ["all"])

    items: list[dict] = []
    chart = None
    try:
        raw_items = client.dynamics(
            phrase, period="daily",
            from_date=(today - timedelta(days=35)).isoformat(),
            to_date=today.isoformat(),
            regions=regions, devices=devices,
        )
        # Filter to dates with complete data (accounting for ~3-day lag)
        cutoff = today - timedelta(days=_DATA_LAG)
        items = [i for i in raw_items if date.fromisoformat(i["date"]) <= cutoff]
    except Exception as exc:  # noqa: BLE001
        lines.append(f"❌ Ошибка динамики: {escape_html(str(exc))}")

    if items:
        # 1. Last 7 days table
        lines += format_daily_dynamics(phrase, items)
        lines.append("")

        # 2. Week-over-week (only on Mondays)
        if today.weekday() == 0:
            wow = format_wow_comparison(phrase, items)
            if wow:
                lines += wow
                lines.append("")

        # 3. Day-of-week profile
        profile = format_weekday_profile(items)
        if profile:
            lines += profile
            lines.append("")

        # 4. Anomaly detector
        anomalies = format_anomalies(items)
        if anomalies:
            lines += anomalies
            lines.append("")

        # 5. 30-day totals
        last30 = items[-30:]
        if last30:
            total_30 = sum(i.get("count", 0) for i in last30)
            avg_30 = total_30 / len(last30)
            lines.append(
                f"📈 За {len(last30)} дней: {_fmt_number(total_30)} запросов  "
                f"(в среднем {_fmt_number(avg_30)}/день)"
            )
            lines.append("")

        # 6. Chart
        chart = generate_daily_chart(phrase, items)

    return "\n".join(lines).rstrip(), chart


async def generate_daily_compact_report(
    client: WordstatClient, cfg: dict
) -> "tuple[str, object | None]":
    """Async wrapper — compact daily digest. Returns (report_text, chart_or_None)."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_generate_daily_compact_report, client, cfg)
