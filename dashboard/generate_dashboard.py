#!/usr/bin/env python3
"""AXIS Dashboard Generator — собирает данные и генерирует HTML"""

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ = timezone(timedelta(hours=5))
NOW = datetime.now(TZ)
AGENTS_DIR = Path("/home/axis/openclaw/agents")
STATE_FILE = Path("/home/axis/openclaw/axis-system/axis-state.json")
OUTPUT = Path(__file__).parent / "index.html"

CORE_AGENTS = ["main", "ops", "tech", "devops", "sales", "finance", "shket", "hr", "qc", "draftsman", "team", "strategy"]
TEAM = [
    {"name": "Руслан", "username": "@axis_ceo"},
    {"name": "Мирас", "id": "MEMBER1_TELEGRAM_ID", "username": "@MIKA721S"},
    {"name": "Бахытжан", "id": "MEMBER2_TELEGRAM_ID", "username": "@Sagimbayev"},
]


def load_trello():
    """Load Trello data from axis-state.json"""
    if not STATE_FILE.exists():
        return []
    with open(STATE_FILE) as f:
        data = json.load(f)
    cards = []
    prod = data.get("trello", {}).get("production", {})
    for lst, items in prod.items():
        if not isinstance(items, list):
            continue
        for card in items:
            due = card.get("due")
            status = "🟢"
            due_str = "—"
            overdue = False
            if due:
                try:
                    due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
                    due_str = due_dt.strftime("%d.%m.%Y")
                    days_left = (due_dt - NOW).days
                    if days_left < 0:
                        status = "🔴"
                        overdue = True
                    elif days_left < 3:
                        status = "🟡"
                except Exception:
                    due_str = due
            cards.append({
                "name": card.get("name", "—"),
                "list": lst,
                "due": due_str,
                "status": status,
                "overdue": overdue,
            })
    return cards


def load_agents():
    """Check MEMORY.md freshness and SOUL.md size for each agent"""
    agents = []
    for name in CORE_AGENTS:
        agent_dir = AGENTS_DIR / name
        memory = agent_dir / "MEMORY.md"
        soul = agent_dir / "SOUL.md"

        soul_lines = 0
        if soul.exists():
            soul_lines = len(soul.read_text(errors="ignore").splitlines())

        memory_date = "—"
        memory_status = "🔴"
        memory_size = 0
        if memory.exists():
            mtime = datetime.fromtimestamp(memory.stat().st_mtime, tz=TZ)
            memory_date = mtime.strftime("%d.%m %H:%M")
            memory_size = memory.stat().st_size
            hours_ago = (NOW - mtime).total_seconds() / 3600
            if hours_ago < 24:
                memory_status = "🟢"
            elif hours_ago < 48:
                memory_status = "🟡"
            else:
                memory_status = "🔴"

        agents.append({
            "name": name,
            "soul_lines": soul_lines,
            "memory_date": memory_date,
            "memory_status": memory_status,
            "memory_size": memory_size,
        })
    return agents


def load_cron():
    """Load cron jobs from openclaw CLI"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            jobs = data if isinstance(data, list) else data.get("jobs", [])
            return [j for j in jobs if j.get("enabled", True)]
    except Exception:
        pass
    return []


def load_kpi():
    """Load KPI data from kpi-trello-check.py"""
    try:
        result = subprocess.run(
            ["python3", "/home/axis/openclaw/scripts/kpi-trello-check.py", "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def score_icon(s):
    if s is None:
        return "⚪"
    try:
        s = float(s)
    except Exception:
        return "⚪"
    if s >= 80:
        return "🟢"
    if s > 0:
        return "🟡"
    return "🔴"


def generate_html(cards, agents, cron_jobs, kpi):
    """Generate the dashboard HTML"""

    # ── Trello rows ──────────────────────────────────────────────────────────
    trello_rows = ""
    for c in cards:
        if "ШАБЛОН" in c["name"] and c["list"] == "Бэклог":
            continue
        css_class = "row-error" if c["overdue"] else ""
        name_esc = c["name"][:60].replace("<", "&lt;").replace(">", "&gt;")
        trello_rows += f"""
        <tr class="{css_class}">
            <td>{name_esc}</td>
            <td>{c['list']}</td>
            <td>{c['due']}</td>
            <td class="status">{c['status']}</td>
        </tr>"""

    if not trello_rows:
        trello_rows = '<tr><td colspan="4" style="text-align:center;color:#8b949e">Нет данных</td></tr>'

    # ── KPI rows ─────────────────────────────────────────────────────────────
    kpi_rows = ""
    overall_score_val = None
    if kpi:
        t = kpi.get("trello", {})
        b = kpi.get("briefing", {})
        p = kpi.get("plan_report", {})
        o = kpi.get("overall", {})
        overall_score_val = o.get("available_score")

        kpi_rows = f"""
        <tr>
            <td>📋 Trello</td>
            <td class="status">{score_icon(t.get('score'))} {t.get('score', '?')}%</td>
            <td>Просрочено: {t.get('overdue', '?')} | Зависших: {t.get('stale_cards', '?')}</td>
        </tr>
        <tr>
            <td>📝 Утренний брифинг</td>
            <td class="status">{score_icon(b.get('score'))} {b.get('score', '?')}%</td>
            <td>{b.get('note', '—')}</td>
        </tr>
        <tr>
            <td>📊 План-отчёт</td>
            <td class="status">{score_icon(p.get('score'))} {p.get('score', '?')}%</td>
            <td>{p.get('note', '—')}</td>
        </tr>
        <tr style="font-weight:bold;border-top:2px solid #30363d;">
            <td>ОБЩИЙ БАЛЛ</td>
            <td class="status" style="font-size:18px;">{score_icon(overall_score_val)} {overall_score_val if overall_score_val is not None else '?'}%</td>
            <td>{o.get('data_completeness', '—')}</td>
        </tr>"""
    else:
        kpi_rows = '<tr><td colspan="3" style="text-align:center;color:#8b949e">KPI данные недоступны</td></tr>'

    overall_score_display = f"{overall_score_val}%" if overall_score_val is not None else "—"

    # ── Agent rows ────────────────────────────────────────────────────────────
    agent_rows = ""
    for a in agents:
        soul_warn = " ⚠️" if a["soul_lines"] > 200 else ""
        size_kb = f"{a['memory_size'] // 1024}KB" if a["memory_size"] else "0KB"
        agent_rows += f"""
        <tr>
            <td>{a['name']}</td>
            <td>{a['soul_lines']}{soul_warn}</td>
            <td>{a['memory_date']}</td>
            <td>{size_kb}</td>
            <td class="status">{a['memory_status']}</td>
        </tr>"""

    # ── Cron rows ─────────────────────────────────────────────────────────────
    cron_rows = ""
    for j in cron_jobs[:20]:
        name = str(j.get("name", "—"))[:45].replace("<", "&lt;")
        state = j.get("state", {})
        last_status = state.get("lastStatus", "—")
        errors = state.get("consecutiveErrors", 0)
        status_icon = "🟢" if last_status == "ok" else ("🔴" if last_status == "error" else "🟡")
        if errors and int(errors) > 0:
            status_icon = "🔴"
        next_run = "—"
        if state.get("nextRunAtMs"):
            try:
                nr = datetime.fromtimestamp(int(state["nextRunAtMs"]) / 1000, tz=TZ)
                next_run = nr.strftime("%d.%m %H:%M")
            except Exception:
                pass
        cron_rows += f"""
        <tr>
            <td>{name}</td>
            <td class="status">{status_icon}</td>
            <td>{errors}</td>
            <td>{next_run}</td>
        </tr>"""

    if not cron_rows:
        cron_rows = '<tr><td colspan="4" style="text-align:center;color:#8b949e">Нет данных</td></tr>'

    # ── Team rows with rituals ──────────────────────────────────────────────
    team_rows = ""
    briefing_data = {}
    if kpi and kpi.get("briefing", {}).get("filled"):
        for name in kpi["briefing"]["filled"]:
            briefing_data[name] = True
    
    rituals = {
        "Руслан": ["Утренний брифинг", "Планёрка Пн", "Ретроспектива Пт"],
        "Мирас": ["Утренний брифинг", "Trello обновление", "План-отчёт Пн"],
        "Бахытжан": ["Утренний брифинг", "Trello обновление", "План-отчёт Пн"],
    }
    
    for member in TEAM:
        name = member["name"]
        briefing_ok = "✅" if briefing_data.get(name) else "❌"
        member_rituals = rituals.get(name, [])
        rituals_html = " · ".join(member_rituals)
        team_rows += f"""
        <tr>
            <td>{name}</td>
            <td>{member.get('username', '—')}</td>
            <td class="status">{briefing_ok}</td>
            <td style="font-size:12px;color:#8b949e">{rituals_html}</td>
        </tr>"""

    # ── Stats ─────────────────────────────────────────────────────────────────
    total_projects = len([c for c in cards if c["list"] in ["В работе", "Очередь"]])
    overdue_count = len([c for c in cards if c["overdue"]])
    healthy_agents = len([a for a in agents if a["memory_status"] == "🟢"])
    agent_health_pct = int(healthy_agents / len(agents) * 100) if agents else 0
    cron_errors = len([j for j in cron_jobs if int(j.get("state", {}).get("consecutiveErrors", 0)) > 0])

    updated = NOW.strftime("%d.%m.%Y %H:%M")

    # ── HTML ──────────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="300">
    <title>AXIS Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 16px;
            min-height: 100vh;
        }}
        .header {{
            text-align: center;
            padding: 20px 0 12px;
            border-bottom: 1px solid #21262d;
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-size: 26px;
            font-weight: 700;
            color: #58a6ff;
            letter-spacing: 2px;
        }}
        .header .updated {{
            font-size: 12px;
            color: #8b949e;
            margin-top: 4px;
        }}

        /* Stats bar */
        .stats-bar {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 24px;
        }}
        .stat-card {{
            flex: 1 1 160px;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: 700;
            color: #58a6ff;
        }}
        .stat-card .value.red {{ color: #f85149; }}
        .stat-card .value.green {{ color: #3fb950; }}
        .stat-card .value.yellow {{ color: #d29922; }}
        .stat-card .label {{
            font-size: 12px;
            color: #8b949e;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Sections */
        .section {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .section-header {{
            background: #21262d;
            padding: 10px 16px;
            font-size: 14px;
            font-weight: 600;
            color: #e6edf3;
            border-bottom: 1px solid #30363d;
        }}
        .section-body {{ padding: 0; }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th {{
            background: #1c2128;
            color: #8b949e;
            font-weight: 600;
            padding: 8px 12px;
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 8px 12px;
            border-top: 1px solid #21262d;
            vertical-align: middle;
        }}
        tr:hover td {{ background: #1c2128; }}
        .row-error td {{ background: rgba(248, 81, 73, 0.08); }}
        .row-error:hover td {{ background: rgba(248, 81, 73, 0.14); }}
        td.status {{ text-align: center; font-size: 16px; }}

        @media (max-width: 600px) {{
            .stat-card {{ flex: 1 1 120px; }}
            .stat-card .value {{ font-size: 24px; }}
            td, th {{ padding: 6px 8px; font-size: 12px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ AXIS DASHBOARD</h1>
        <div class="updated">Обновлено: {updated} (UTC+5) · Auto-refresh: 5 мин</div>
        <div class="updated">Команда: {' · '.join(m['name'] for m in TEAM)}</div>
    </div>

    <!-- Stats bar -->
    <div class="stats-bar">
        <div class="stat-card">
            <div class="value">{total_projects}</div>
            <div class="label">В работе</div>
        </div>
        <div class="stat-card">
            <div class="value {'red' if overdue_count > 0 else 'green'}">{overdue_count}</div>
            <div class="label">Просрочено</div>
        </div>
        <div class="stat-card">
            <div class="value {'green' if agent_health_pct >= 80 else 'yellow' if agent_health_pct >= 50 else 'red'}">{agent_health_pct}%</div>
            <div class="label">Здоровье агентов</div>
        </div>
        <div class="stat-card">
            <div class="value {'green' if overall_score_val and float(overall_score_val) >= 80 else 'yellow' if overall_score_val and float(overall_score_val) > 0 else 'red'}">{overall_score_display}</div>
            <div class="label">KPI балл</div>
        </div>
        <div class="stat-card">
            <div class="value {'red' if cron_errors > 0 else 'green'}">{cron_errors}</div>
            <div class="label">Cron ошибки</div>
        </div>
    </div>

    <!-- Trello -->
    <div class="section">
        <div class="section-header">📋 Trello — Карточки ({len(cards)})</div>
        <div class="section-body">
            <table>
                <tr>
                    <th>Задача</th>
                    <th>Список</th>
                    <th>Срок</th>
                    <th>Статус</th>
                </tr>
                {trello_rows}
            </table>
        </div>
    </div>

    <!-- KPI дисциплины -->
    <div class="section">
        <div class="section-header">📊 KPI Дисциплины (брифинг / Trello / план-отчёт)</div>
        <div class="section-body">
            <table>
                <tr>
                    <th>Категория</th>
                    <th>Балл</th>
                    <th>Детали</th>
                </tr>
                {kpi_rows}
            </table>
        </div>
    </div>

    <!-- Команда -->
    <div class="section">
        <div class="section-header">👥 Команда</div>
        <div class="section-body">
            <table>
                <tr>
                    <th>Имя</th>
                    <th>Telegram</th>
                    <th>Брифинг</th>
                    <th>Ритуалы</th>
                </tr>
                {team_rows}
            </table>
        </div>
    </div>

    <!-- Агенты -->
    <div class="section">
        <div class="section-header">🤖 Агенты AXIS ({len(agents)})</div>
        <div class="section-body">
            <table>
                <tr>
                    <th>Агент</th>
                    <th>SOUL строк</th>
                    <th>MEMORY обновлён</th>
                    <th>Размер</th>
                    <th>Статус</th>
                </tr>
                {agent_rows}
            </table>
        </div>
    </div>

    <!-- Кроны -->
    <div class="section">
        <div class="section-header">⏱ Cron Jobs ({len(cron_jobs)})</div>
        <div class="section-body">
            <table>
                <tr>
                    <th>Имя</th>
                    <th>Статус</th>
                    <th>Ошибки</th>
                    <th>Следующий запуск</th>
                </tr>
                {cron_rows}
            </table>
        </div>
    </div>

</body>
</html>"""
    return html


def main():
    print(f"[{NOW.strftime('%H:%M:%S')}] Генерация AXIS Dashboard...")

    print("  → Загрузка Trello...", end=" ", flush=True)
    cards = load_trello()
    print(f"{len(cards)} карточек")

    print("  → Проверка агентов...", end=" ", flush=True)
    agents = load_agents()
    print(f"{len(agents)} агентов")

    print("  → Загрузка cron...", end=" ", flush=True)
    cron_jobs = load_cron()
    print(f"{len(cron_jobs)} задач")

    print("  → Запуск KPI скрипта...", end=" ", flush=True)
    kpi = load_kpi()
    if kpi:
        score = kpi.get("overall", {}).get("available_score", "?")
        print(f"балл {score}%")
    else:
        print("нет данных")

    print("  → Генерация HTML...")
    html = generate_html(cards, agents, cron_jobs, kpi)

    OUTPUT.write_text(html, encoding="utf-8")
    size_kb = OUTPUT.stat().st_size // 1024
    print(f"  ✅ Готово: {OUTPUT} ({size_kb}KB)")


if __name__ == "__main__":
    main()
