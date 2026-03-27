#!/usr/bin/env python3
"""
AXIS Rituals Dashboard Generator
Reads cron state, team state, and health data → writes rituals-data.json + rituals.html
"""

import json
import os
import sys
import requests
from datetime import datetime, timedelta, date
from pathlib import Path

DASHBOARD_DIR = Path(__file__).parent
RITUALS_DATA = DASHBOARD_DIR / "rituals-data.json"
RITUALS_HTML = DASHBOARD_DIR / "rituals.html"
JOBS_FILE = Path.home() / ".openclaw/cron/jobs.json"
TEAM_STATE = Path("/home/axis/openclaw/team-state.json")
HEALTH_URL = "http://127.0.0.1:18795/health"

CRON_ICONS = {
    "Утренний отчёт Trello": "📋",
    "Утренний пинг команде": "🌅",
    "Дневная проверка Trello": "🔍",
    "Дневная проверка команды": "👥",
    "Вечерний отчёт команды": "🌙",
    "Вечерний отчёт Trello": "📊",
    "Проверка триггеров": "⚡",
    "Проверка Google Forms": "📝",
    "Еженедельная ретроспектива": "🔄",
    "Месячная ретроспектива": "📅",
    "QC аудит агентов": "🛡️",
    "Strategy KPI сбор": "🎯",
    "Daily System Audit": "⚙️",
    "Security Check Weekly": "🔒",
}


def get_days_range(n=7):
    today = date.today()
    return [(today - timedelta(days=n - 1 - i)).isoformat() for i in range(n)]


def read_cron_jobs():
    if not JOBS_FILE.exists():
        return {}
    with open(JOBS_FILE) as f:
        data = json.load(f)
    return {j["name"]: j for j in data.get("jobs", [])}


def read_team_state():
    if not TEAM_STATE.exists():
        return {}
    with open(TEAM_STATE) as f:
        return json.load(f)


def fetch_health():
    try:
        r = requests.get(HEALTH_URL, timeout=5)
        return r.json()
    except Exception:
        return {}


def load_existing_data():
    if RITUALS_DATA.exists():
        with open(RITUALS_DATA) as f:
            return json.load(f)
    return {"days": [], "crons": {}, "people": {}, "system": {}}


def compute_streak(crons_data, days):
    """Count consecutive days (from today backwards) with no errors among active crons.
    A day counts only if at least one cron ran (status != skip). Pure skip days are neutral."""
    streak = 0
    for i in range(len(days) - 1, -1, -1):
        has_error = False
        has_run = False
        for name, info in crons_data.items():
            status = info["statuses"][i] if i < len(info["statuses"]) else "skip"
            if status in ("ok", "pending"):
                has_run = True
            if status in ("error",):
                has_error = True
                break
        if has_error:
            break
        if has_run:
            streak += 1
        # skip days don't increment but also don't break streak
    return streak


def compute_person_streak(last_response_str, today_str):
    """Count how many consecutive days person responded up to today."""
    if not last_response_str:
        return 0
    try:
        last = datetime.fromisoformat(last_response_str).date()
        today = date.fromisoformat(today_str)
        delta = (today - last).days
        # Simple: if responded today or yesterday = streak continues
        # We don't have full history, so estimate from last_response
        if delta == 0:
            return 1
        return 0
    except Exception:
        return 0


def generate_data():
    days = get_days_range(7)
    today_str = days[-1]
    now_str = datetime.now().isoformat(timespec="seconds")

    jobs = read_cron_jobs()
    team = read_team_state()
    health = fetch_health()
    existing = load_existing_data()

    # ── CRONS ──────────────────────────────────────────────────────────────
    # Build crons dict. For existing days reuse history, for today update from live state.
    crons_out = {}
    for name, job in jobs.items():
        icon = CRON_ICONS.get(name, "🔧")
        agent = job.get("agentId", "?")
        state = job.get("state", {})
        enabled = job.get("enabled", True)

        # Determine today's status from live cron state
        last_run_at_ms = state.get("lastRunAtMs")
        last_status = state.get("lastRunStatus") or state.get("lastStatus", "unknown")
        consecutive_errors = state.get("consecutiveErrors", 0)

        if not enabled:
            today_status = "skip"
        elif last_run_at_ms:
            last_run_date = datetime.fromtimestamp(last_run_at_ms / 1000).date().isoformat()
            if last_run_date == today_str:
                if last_status == "ok":
                    today_status = "ok"
                elif consecutive_errors > 0:
                    today_status = "error"
                else:
                    today_status = "pending"
            else:
                # Ran before today — mark today as not yet run
                # Check if cron is scheduled for today
                today_status = "pending"
        else:
            today_status = "skip"

        # Rebuild 7-day history
        statuses = []
        prev = existing.get("crons", {}).get(name, {})
        prev_statuses = prev.get("statuses", [])
        prev_days = existing.get("days", [])

        for d in days:
            if d == today_str:
                statuses.append(today_status)
            elif d in prev_days:
                idx = prev_days.index(d)
                if idx < len(prev_statuses):
                    statuses.append(prev_statuses[idx])
                else:
                    statuses.append("skip")
            else:
                statuses.append("skip")

        crons_out[name] = {"statuses": statuses, "agent": agent, "icon": icon}

    # ── PEOPLE ─────────────────────────────────────────────────────────────
    people_out = {}
    employees = team.get("employees", {})
    for uid, emp in employees.items():
        name = emp.get("name", uid)
        last_response = emp.get("last_response", "")
        # Determine today's status
        today_status = "silent"
        if last_response:
            try:
                lr_date = datetime.fromisoformat(last_response).date()
                today_date = date.fromisoformat(today_str)
                if lr_date == today_date:
                    today_status = "active"
                elif (today_date - lr_date).days <= 1:
                    today_status = "active"
            except Exception:
                pass

        # Streak: count based on last_response closeness
        streak = compute_person_streak(last_response, today_str)
        lr_display = ""
        if last_response:
            try:
                lr_display = datetime.fromisoformat(last_response).strftime("%d.%m.%Y %H:%M")
            except Exception:
                lr_display = last_response

        people_out[name] = {
            "last_response": last_response,
            "last_response_display": lr_display,
            "streak": streak,
            "today": today_status,
        }

    # ── SYSTEM ─────────────────────────────────────────────────────────────
    ram = health.get("ram", {})
    disk = health.get("disk", {})
    errors_today = 0
    try:
        log_path = Path("/tmp/monitor.log")
        if log_path.exists():
            content = log_path.read_text(errors="ignore")
            today_prefix = today_str
            errors_today = content.count("ERROR") + content.count("CRITICAL")
    except Exception:
        pass

    system_out = {
        "uptime": health.get("uptime", "?"),
        "ram_percent": round(ram.get("percent", 0)),
        "disk_percent": round(disk.get("percent", 0)),
        "errors_today": errors_today,
        "backup_ok": True,
        "status": health.get("status", "unknown"),
    }

    # ── ASSEMBLE ───────────────────────────────────────────────────────────
    streak = compute_streak(crons_out, days)

    data = {
        "generated": now_str,
        "days": days,
        "streak": streak,
        "crons": crons_out,
        "people": people_out,
        "system": system_out,
    }

    with open(RITUALS_DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ rituals-data.json updated ({now_str})")
    return data


def render_html(data):
    days = data["days"]
    streak = data["streak"]
    generated = data["generated"]
    crons = data["crons"]
    people = data["people"]
    system = data["system"]

    # Format days as short names
    day_names_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    def day_label(d):
        dt = date.fromisoformat(d)
        return day_names_ru[dt.weekday()]

    def day_short(d):
        dt = date.fromisoformat(d)
        return dt.strftime("%d.%m")

    # Status → display
    STATUS_HTML = {
        "ok": ('<div class="cell ok" title="OK">✅</div>'),
        "error": ('<div class="cell error" title="Ошибка">❌</div>'),
        "skip": ('<div class="cell skip" title="Не запускался">⬜</div>'),
        "pending": ('<div class="cell pending" title="Запущен, нет данных">🟡</div>'),
        "unknown": ('<div class="cell skip" title="Неизвестно">⬜</div>'),
    }

    def status_cell(s):
        return STATUS_HTML.get(s, STATUS_HTML["skip"])

    # Build cron table rows
    cron_rows = ""
    for name, info in crons.items():
        icon = info.get("icon", "🔧")
        agent = info.get("agent", "?")
        statuses = info.get("statuses", ["skip"] * 7)
        cells = "".join(status_cell(s) for s in statuses)
        agent_badge = f'<span class="agent-badge">{agent}</span>'
        cron_rows += f"""
        <tr>
          <td class="cron-name">{icon} {name} {agent_badge}</td>
          {chr(10).join(f'<td class="cell-wrap">{status_cell(s)}</td>' for s in statuses)}
        </tr>"""

    # Build people blocks
    people_blocks = ""
    for name, info in people.items():
        today = info.get("today", "silent")
        streak_val = info.get("streak", 0)
        lr = info.get("last_response_display", "—")

        if today == "active":
            status_class = "person-active"
            status_icon = "🟢"
            status_text = "Ответил сегодня"
        elif today == "silent":
            status_class = "person-silent"
            status_icon = "🔴"
            status_text = "Молчит"
        else:
            status_class = "person-off"
            status_icon = "⬜"
            status_text = "Выходной"

        people_blocks += f"""
      <div class="person-card {status_class}">
        <div class="person-header">
          <span class="person-icon">{status_icon}</span>
          <span class="person-name">{name}</span>
        </div>
        <div class="person-meta">
          <div class="person-row"><span class="label">Статус:</span> {status_text}</div>
          <div class="person-row"><span class="label">Последний ответ:</span> {lr}</div>
          <div class="person-row"><span class="label">Streak:</span> {streak_val} дн.</div>
        </div>
      </div>"""

    # System block
    ram_pct = system.get("ram_percent", 0)
    disk_pct = system.get("disk_percent", 0)
    errors = system.get("errors_today", 0)
    uptime = system.get("uptime", "?")
    backup = system.get("backup_ok", True)
    backup_icon = "✅" if backup else "❌"
    errors_class = "metric-ok" if errors == 0 else "metric-error"
    ram_class = "metric-ok" if ram_pct < 70 else ("metric-warn" if ram_pct < 90 else "metric-error")
    disk_class = "metric-ok" if disk_pct < 70 else ("metric-warn" if disk_pct < 90 else "metric-error")

    # Day header row
    day_headers = "".join(
        f'<th class="day-header"><div class="day-name">{day_label(d)}</div><div class="day-date">{day_short(d)}</div></th>'
        for d in days
    )

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="300">
<title>⚡ Ритуалы AXIS</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    background: #1a1a2e;
    font-family: 'Press Start 2P', monospace;
    color: #e0e0e0;
    min-height: 100vh;
    overflow-x: hidden;
}}

/* ── HEADER ─────────────────────────────────────── */
.header {{
    text-align: center;
    padding: 24px 16px 16px;
    background: linear-gradient(180deg, #16213e 0%, #1a1a2e 100%);
    border-bottom: 4px solid #0f3460;
    position: relative;
}}

.header h1 {{
    font-size: clamp(10px, 2.5vw, 16px);
    color: #6366f1;
    text-shadow: 3px 3px 0 #000, 0 0 20px rgba(99,102,241,0.4);
    margin-bottom: 12px;
    letter-spacing: 2px;
}}

.header-meta {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
}}

.meta-chip {{
    font-size: 7px;
    color: #8b8fa3;
    background: #16213e;
    border: 2px solid #0f3460;
    padding: 4px 10px;
    border-radius: 4px;
}}

.streak-chip {{
    font-size: 8px;
    color: #ffd700;
    background: #1a1a2e;
    border: 2px solid #ffd700;
    padding: 6px 14px;
    border-radius: 4px;
    text-shadow: 0 0 8px rgba(255,215,0,0.6);
    box-shadow: 0 0 10px rgba(255,215,0,0.2);
}}

/* ── MAIN CONTENT ────────────────────────────────── */
.content {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 20px 12px 40px;
}}

/* ── SECTION ─────────────────────────────────────── */
.section {{
    margin-bottom: 28px;
}}

.section-title {{
    font-size: 9px;
    color: #6366f1;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #0f3460;
    text-shadow: 0 0 10px rgba(99,102,241,0.5);
}}

/* ── CRON TABLE ──────────────────────────────────── */
.table-wrap {{
    overflow-x: auto;
    border: 3px solid #0f3460;
    border-radius: 6px;
    background: #16213e;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    min-width: 500px;
}}

thead th {{
    background: #0f3460;
    padding: 8px 4px;
}}

.day-header {{
    text-align: center;
    width: 68px;
}}

.day-name {{
    font-size: 8px;
    color: #6366f1;
}}

.day-date {{
    font-size: 6px;
    color: #8b8fa3;
    margin-top: 2px;
}}

.cron-name-header {{
    font-size: 7px;
    color: #8b8fa3;
    text-align: left;
    padding-left: 12px;
    min-width: 200px;
}}

tbody tr {{
    border-bottom: 1px solid #0f346040;
    transition: background 0.2s;
}}

tbody tr:hover {{
    background: #0f3460aa;
}}

tbody tr:last-child {{
    border-bottom: none;
}}

.cron-name {{
    font-size: 6px;
    color: #c0c0d0;
    padding: 8px 12px;
    white-space: nowrap;
    min-width: 220px;
}}

.agent-badge {{
    font-size: 5px;
    color: #6366f1;
    background: #0f3460;
    padding: 2px 5px;
    border-radius: 3px;
    margin-left: 4px;
    vertical-align: middle;
}}

.cell-wrap {{
    text-align: center;
    padding: 6px 4px;
}}

.cell {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 6px;
    font-size: 18px;
    cursor: default;
    transition: transform 0.15s, box-shadow 0.15s;
    border: 2px solid transparent;
}}

.cell:hover {{
    transform: scale(1.15);
}}

.cell.ok {{
    background: #1a3a1a;
    border-color: #22c55e;
    box-shadow: 0 0 8px rgba(34,197,94,0.3);
}}

.cell.error {{
    background: #3a1a1a;
    border-color: #ef4444;
    box-shadow: 0 0 8px rgba(239,68,68,0.3);
}}

.cell.skip {{
    background: #2a2a3a;
    border-color: #4a4a6a;
}}

.cell.pending {{
    background: #3a3010;
    border-color: #eab308;
    box-shadow: 0 0 8px rgba(234,179,8,0.3);
}}

/* ── PEOPLE ──────────────────────────────────────── */
.people-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 16px;
}}

.person-card {{
    border: 3px solid #0f3460;
    border-radius: 8px;
    padding: 16px;
    background: #16213e;
    transition: box-shadow 0.2s;
}}

.person-card:hover {{
    box-shadow: 0 0 20px rgba(99,102,241,0.2);
}}

.person-card.person-active {{
    border-color: #22c55e;
    box-shadow: 0 0 12px rgba(34,197,94,0.2);
}}

.person-card.person-silent {{
    border-color: #ef4444;
    box-shadow: 0 0 12px rgba(239,68,68,0.15);
}}

.person-card.person-off {{
    border-color: #4a4a6a;
}}

.person-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #0f3460;
}}

.person-icon {{
    font-size: 20px;
}}

.person-name {{
    font-size: 9px;
    color: #e0e0e0;
}}

.person-meta {{
    display: flex;
    flex-direction: column;
    gap: 8px;
}}

.person-row {{
    font-size: 6px;
    color: #8b8fa3;
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}}

.person-row .label {{
    color: #6366f1;
}}

/* ── SYSTEM ──────────────────────────────────────── */
.system-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
}}

.metric-card {{
    border: 3px solid #0f3460;
    border-radius: 8px;
    padding: 14px;
    background: #16213e;
    text-align: center;
}}

.metric-label {{
    font-size: 6px;
    color: #8b8fa3;
    margin-bottom: 8px;
    letter-spacing: 1px;
}}

.metric-value {{
    font-size: 13px;
    text-shadow: 0 0 10px currentColor;
}}

.metric-ok {{ color: #22c55e; }}
.metric-warn {{ color: #eab308; }}
.metric-error {{ color: #ef4444; }}
.metric-info {{ color: #6366f1; }}

.bar-wrap {{
    margin-top: 8px;
    background: #0f3460;
    border-radius: 4px;
    height: 6px;
    overflow: hidden;
}}

.bar {{
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s;
}}

.bar.ok {{ background: #22c55e; }}
.bar.warn {{ background: #eab308; }}
.bar.err {{ background: #ef4444; }}

/* ── LEGEND ──────────────────────────────────────── */
.legend {{
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    font-size: 6px;
    color: #8b8fa3;
    margin-top: 10px;
    align-items: center;
}}

.legend-item {{
    display: flex;
    align-items: center;
    gap: 6px;
}}

.legend-dot {{
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 2px solid transparent;
}}
.legend-dot.ok {{ background: #1a3a1a; border-color: #22c55e; }}
.legend-dot.error {{ background: #3a1a1a; border-color: #ef4444; }}
.legend-dot.skip {{ background: #2a2a3a; border-color: #4a4a6a; }}
.legend-dot.pending {{ background: #3a3010; border-color: #eab308; }}

/* ── FOOTER ──────────────────────────────────────── */
footer {{
    text-align: center;
    font-size: 6px;
    color: #4a4a6a;
    padding: 16px;
    border-top: 2px solid #0f3460;
    margin-top: 20px;
}}

footer span {{
    color: #6366f1;
}}

/* ── RESPONSIVE ──────────────────────────────────── */
@media (max-width: 600px) {{
    .header h1 {{ font-size: 9px; }}
    .cell {{ width: 32px; height: 32px; font-size: 14px; }}
    .cron-name {{ font-size: 5px; padding: 6px 8px; }}
    .day-header {{ width: 50px; }}
    .people-grid {{ grid-template-columns: 1fr; }}
    .system-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}

/* ── SCAN LINE FX ─────────────────────────────────── */
body::after {{
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.03) 2px,
        rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
}}
</style>
</head>
<body>

<div class="header">
  <h1>⚡ РИТУАЛЫ УПРАВЛЕНИЯ AXIS</h1>
  <div class="header-meta">
    <div class="meta-chip">📅 {generated[:10]}</div>
    <div class="meta-chip">🕐 {generated[11:16]}</div>
    <div class="streak-chip">🔥 STREAK: {streak} дн.</div>
  </div>
</div>

<div class="content">

  <!-- CRON TABLE -->
  <div class="section">
    <div class="section-title">📡 Кроны · Трекер Ритуалов</div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th class="cron-name-header">Ритуал</th>
            {day_headers}
          </tr>
        </thead>
        <tbody>
          {cron_rows}
        </tbody>
      </table>
    </div>
    <div class="legend">
      <span>Легенда:</span>
      <div class="legend-item"><div class="legend-dot ok"></div> ✅ OK</div>
      <div class="legend-item"><div class="legend-dot error"></div> ❌ Ошибка</div>
      <div class="legend-item"><div class="legend-dot skip"></div> ⬜ Не запускался</div>
      <div class="legend-item"><div class="legend-dot pending"></div> 🟡 Нет данных</div>
    </div>
  </div>

  <!-- PEOPLE -->
  <div class="section">
    <div class="section-title">👥 Люди · Активность Команды</div>
    <div class="people-grid">
      {people_blocks}
    </div>
  </div>

  <!-- SYSTEM HEALTH -->
  <div class="section">
    <div class="section-title">🛡️ Здоровье Системы</div>
    <div class="system-grid">

      <div class="metric-card">
        <div class="metric-label">⏱️ UPTIME</div>
        <div class="metric-value metric-ok">{uptime}</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">🧠 RAM</div>
        <div class="metric-value {ram_class}">{ram_pct}%</div>
        <div class="bar-wrap">
          <div class="bar {"ok" if ram_pct < 70 else "warn" if ram_pct < 90 else "err"}" style="width:{ram_pct}%"></div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-label">💾 DISK</div>
        <div class="metric-value {disk_class}">{disk_pct}%</div>
        <div class="bar-wrap">
          <div class="bar {"ok" if disk_pct < 70 else "warn" if disk_pct < 90 else "err"}" style="width:{disk_pct}%"></div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-label">⚠️ ОШИБОК СЕГОДНЯ</div>
        <div class="metric-value {errors_class}">{errors}</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">💿 БЭКАП</div>
        <div class="metric-value {"metric-ok" if backup else "metric-error"}">{backup_icon}</div>
      </div>

    </div>
  </div>

</div>

<footer>
  Auto-refresh 5 min &nbsp;•&nbsp; <span>Powered by OpenClaw</span> &nbsp;•&nbsp; Обновлено: {generated}
</footer>

</body>
</html>"""

    with open(RITUALS_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ rituals.html generated ({len(html)} bytes)")


if __name__ == "__main__":
    print("🔄 Generating AXIS Rituals Dashboard...")
    data = generate_data()
    render_html(data)
    print("✅ Done!")
