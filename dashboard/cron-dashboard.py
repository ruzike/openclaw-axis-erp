#!/usr/bin/env python3
"""
AXIS Automation Dashboard — визуализация всех cron-задач и их статусов.
Генерирует HTML страницу с real-time данными.
"""

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ = timezone(timedelta(hours=5))
NOW = datetime.now(TZ)
OUTPUT = Path(__file__).parent / "automation.html"
JOBS_FILE = Path(os.path.expanduser("~/.openclaw/cron/jobs.json"))

def get_openclaw_crons():
    """Читаем OpenClaw cron jobs"""
    if not JOBS_FILE.exists():
        return []
    with open(JOBS_FILE) as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get('jobs', [])

def get_system_crons():
    """Читаем системный crontab"""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=5)
        lines = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('OPENAI') and not line.startswith('PATH'):
                # Parse cron line
                parts = line.split(None, 5)
                if len(parts) >= 6:
                    schedule = ' '.join(parts[:5])
                    command = parts[5]
                    # Extract script name
                    name = "Unknown"
                    if 'monitor.py' in command: name = "Системный монитор"
                    elif 'check-due-dates' in command: name = "Проверка сроков Trello"
                    elif 'send-reminders' in command: name = "Напоминания Trello"
                    elif 'ingress' in command: name = "Ingress — входящие задачи"
                    elif 'semantic-index' in command: name = "Семантическая индексация"
                    elif 'find /tmp' in command: name = "Очистка логов"
                    elif 'generate-report' in command: name = "Пятничный отчёт Trello"
                    elif 'backup' in command: name = "Бэкап конфигов"
                    elif 'cron-monitor' in command: name = "Cron Monitor"
                    elif 'dashboard' in command: name = "Dashboard обновление"
                    lines.append({'name': name, 'schedule': schedule, 'command': command})
        return lines
    except:
        return []

def get_healthcheck():
    """Получаем данные healthcheck"""
    try:
        import urllib.request
        resp = urllib.request.urlopen('http://127.0.0.1:18795/health', timeout=3)
        return json.loads(resp.read())
    except:
        return None

def format_time(ms):
    if not ms or ms == 0:
        return "—"
    dt = datetime.fromtimestamp(ms / 1000, tz=TZ)
    return dt.strftime("%d.%m %H:%M")

def format_duration(ms):
    if not ms: return "—"
    s = ms / 1000
    if s < 60: return f"{s:.0f}с"
    return f"{s/60:.1f}м"

def time_ago(ms):
    if not ms or ms == 0: return "никогда"
    diff = (NOW - datetime.fromtimestamp(ms/1000, tz=TZ)).total_seconds()
    if diff < 60: return "только что"
    if diff < 3600: return f"{diff/60:.0f} мин назад"
    if diff < 86400: return f"{diff/3600:.0f}ч назад"
    return f"{diff/86400:.0f}д назад"

def status_badge(state):
    status = state.get('lastStatus', state.get('lastRunStatus', ''))
    errors = state.get('consecutiveErrors', 0)
    last_run = state.get('lastRunAtMs', 0)
    
    if errors > 0:
        return '<span class="badge badge-error">❌ Ошибка</span>'
    if status == 'ok':
        return '<span class="badge badge-ok">✅ OK</span>'
    if last_run == 0:
        return '<span class="badge badge-idle">⏳ Ожидает</span>'
    return '<span class="badge badge-ok">✅ OK</span>'

def generate_html():
    oc_jobs = get_openclaw_crons()
    sys_crons = get_system_crons()
    health = get_healthcheck()
    
    # Separate by category
    business_jobs = [j for j in oc_jobs if j.get('agentId') == 'main']
    system_jobs = [j for j in oc_jobs if j.get('agentId') != 'main']
    
    # Stats
    total_oc = len(oc_jobs)
    total_sys = len(sys_crons)
    errors = sum(1 for j in oc_jobs if j.get('state', {}).get('consecutiveErrors', 0) > 0)
    ok_count = sum(1 for j in oc_jobs if j.get('state', {}).get('lastStatus') == 'ok')
    idle_count = sum(1 for j in oc_jobs if j.get('state', {}).get('lastRunAtMs', 0) == 0)
    
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="300">
<title>AXIS Automation Dashboard</title>
<style>
:root {{
    --bg: #0f1117;
    --card: #1a1d28;
    --border: #2a2d3a;
    --text: #e0e0e0;
    --text-dim: #8b8fa3;
    --accent: #6366f1;
    --green: #22c55e;
    --red: #ef4444;
    --yellow: #f59e0b;
    --blue: #3b82f6;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ 
    font-family: 'Inter', -apple-system, sans-serif; 
    background: var(--bg); 
    color: var(--text);
    padding: 20px;
    max-width: 1400px;
    margin: 0 auto;
}}
.header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
}}
.header h1 {{ font-size: 24px; font-weight: 700; }}
.header .time {{ color: var(--text-dim); font-size: 14px; }}
.stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
}}
.stat {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}}
.stat .number {{ font-size: 32px; font-weight: 700; }}
.stat .label {{ font-size: 12px; color: var(--text-dim); margin-top: 4px; }}
.stat.green .number {{ color: var(--green); }}
.stat.red .number {{ color: var(--red); }}
.stat.yellow .number {{ color: var(--yellow); }}
.stat.blue .number {{ color: var(--blue); }}
.section {{ margin-bottom: 24px; }}
.section h2 {{
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.table-wrap {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
}}
table {{ width: 100%; border-collapse: collapse; }}
th {{
    text-align: left;
    padding: 10px 14px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-dim);
    background: rgba(255,255,255,0.03);
    border-bottom: 1px solid var(--border);
}}
td {{
    padding: 10px 14px;
    font-size: 13px;
    border-bottom: 1px solid var(--border);
}}
tr:last-child td {{ border-bottom: none; }}
tr:hover {{ background: rgba(255,255,255,0.02); }}
.badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
}}
.badge-ok {{ background: rgba(34,197,94,0.15); color: var(--green); }}
.badge-error {{ background: rgba(239,68,68,0.15); color: var(--red); }}
.badge-idle {{ background: rgba(245,158,11,0.15); color: var(--yellow); }}
.badge-sys {{ background: rgba(59,130,246,0.15); color: var(--blue); }}
.schedule {{ font-family: monospace; font-size: 11px; color: var(--text-dim); }}
.purpose {{ font-size: 12px; color: var(--text-dim); max-width: 300px; }}
.health-bar {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
}}
.health-item {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.health-item .name {{ font-size: 13px; }}
.health-item .val {{ font-weight: 600; font-size: 14px; }}
.footer {{ 
    text-align: center; 
    color: var(--text-dim); 
    font-size: 11px; 
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
}}
</style>
</head>
<body>

<div class="header">
    <h1>⚡ AXIS Automation Dashboard</h1>
    <div class="time">Обновлено: {NOW.strftime('%d.%m.%Y %H:%M')} (Qyzylorda)</div>
</div>

<!-- STATS -->
<div class="stats">
    <div class="stat blue"><div class="number">{total_oc + total_sys}</div><div class="label">Всего задач</div></div>
    <div class="stat green"><div class="number">{ok_count}</div><div class="label">Успешных</div></div>
    <div class="stat yellow"><div class="number">{idle_count}</div><div class="label">Ожидают</div></div>
    <div class="stat red"><div class="number">{errors}</div><div class="label">С ошибками</div></div>
    <div class="stat blue"><div class="number">{total_oc}</div><div class="label">OpenClaw</div></div>
    <div class="stat blue"><div class="number">{total_sys}</div><div class="label">System</div></div>
</div>
"""
    
    # Health bar
    if health:
        html += '<div class="health-bar">'
        html += f'<div class="health-item"><span class="name">🖥 Сервер</span><span class="val" style="color:var(--green)">{health.get("uptime","?")}</span></div>'
        html += f'<div class="health-item"><span class="name">💾 RAM</span><span class="val">{health.get("ram",{}).get("percent","?")}%</span></div>'
        html += f'<div class="health-item"><span class="name">💽 Disk</span><span class="val">{health.get("disk",{}).get("percent","?")}%</span></div>'
        html += f'<div class="health-item"><span class="name">🔒 Статус</span><span class="val" style="color:var(--green)">{health.get("status","?")}</span></div>'
        html += '</div>'

    # Business crons
    purposes = {
        'Утренний отчёт Trello': 'Статус задач на досках — что в работе, что просрочено',
        'Утренний пинг команде': 'Мирас и Бахытжан получают свои задачи на день',
        'Проверка триггеров': 'Каждые 2ч — проверка зависших задач, эскалация',
        'Дневная проверка Trello': 'Промежуточный статус + просроченные задачи',
        'Дневная проверка команды': 'Пинг прогресса сотрудникам',
        'Вечерний отчёт команды': 'Запрос итогов дня у Мираса и Бахытжана',
        'Вечерний отчёт Trello': 'Итоговая статистика: закрыто/перенесено/отставания',
        'QC аудит агентов': 'Проверка MEMORY.md, протоколов, дисциплины агентов',
        'Daily System Audit': 'Аудит сервера: процессы, диск, RAM, логи',
        'Security Check Weekly': 'Входы SSH, fail2ban, порты, обновления',
        'Проверка Google Forms': 'Кто заполнил план-отчёт, напоминания',
        'Еженедельная ретроспектива': 'Итоги недели: плюсы, минусы, дельтаплюсы',
        'Месячная ретроспектива': 'Итоги месяца, карточки в Trello из дельтаплюсов',
        'Strategy KPI сбор': 'Сбор метрик: задачи, проекты, активность',
    }
    
    html += '<div class="section"><h2>📋 Бизнес-автоматизация (OpenClaw)</h2><div class="table-wrap"><table>'
    html += '<tr><th>Статус</th><th>Название</th><th>Расписание</th><th>Зачем нужен</th><th>Последний запуск</th><th>Время</th></tr>'
    
    for job in sorted(oc_jobs, key=lambda j: j.get('schedule', {}).get('expr', '')):
        state = job.get('state', {})
        name = job.get('name', '?')
        schedule = job.get('schedule', {}).get('expr', '?')
        purpose = purposes.get(name, '')
        last_run = state.get('lastRunAtMs', 0)
        duration = state.get('lastDurationMs', 0)
        
        html += f'<tr>'
        html += f'<td>{status_badge(state)}</td>'
        html += f'<td><strong>{name}</strong></td>'
        html += f'<td><span class="schedule">{schedule}</span></td>'
        html += f'<td><span class="purpose">{purpose}</span></td>'
        html += f'<td>{time_ago(last_run)}</td>'
        html += f'<td>{format_duration(duration)}</td>'
        html += f'</tr>'
    
    html += '</table></div></div>'
    
    # System crons
    html += '<div class="section"><h2>🖥 Системный Crontab</h2><div class="table-wrap"><table>'
    html += '<tr><th>Статус</th><th>Название</th><th>Расписание</th></tr>'
    
    for cron in sys_crons:
        html += f'<tr>'
        html += f'<td><span class="badge badge-sys">🔄 Active</span></td>'
        html += f'<td><strong>{cron["name"]}</strong></td>'
        html += f'<td><span class="schedule">{cron["schedule"]}</span></td>'
        html += f'</tr>'
    
    html += '</table></div></div>'
    
    html += f'<div class="footer">AXIS Automation Dashboard • {len(oc_jobs)} OpenClaw + {len(sys_crons)} System = {len(oc_jobs)+len(sys_crons)} задач • Auto-refresh 5 мин</div>'
    html += '</body></html>'
    
    return html

if __name__ == '__main__':
    html = generate_html()
    with open(OUTPUT, 'w') as f:
        f.write(html)
    print(f"✅ Dashboard saved: {OUTPUT} ({len(html)} bytes)")
