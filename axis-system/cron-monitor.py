#!/usr/bin/env python3
"""
AXIS Cron Monitor — мониторинг выполнения cron-задач OpenClaw
Алерт в Telegram Руслану (YOUR_TELEGRAM_ID) при сбое или пропуске.

Запуск: python3 cron-monitor.py
Cron: */30 * * * * python3 /home/axis/openclaw/axis-system/cron-monitor.py
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# === КОНФИГ ===
JOBS_FILE = os.path.expanduser("~/.openclaw/cron/jobs.json")
ALERT_USER_ID = "YOUR_TELEGRAM_ID"  # Руслан
TELEGRAM_CHANNEL = "telegram"
LOG_FILE = "/tmp/cron-monitor.log"
ALERT_STATE_FILE = "/tmp/cron-monitor-alerts.json"  # Защита от повторных алертов

# Лимиты
MAX_SILENCE_MULTIPLIER = 2.5   # считаем пропуском если молчит в N раз дольше периода
MAX_CONSECUTIVE_ERRORS = 1     # алерт уже при 1 ошибке
NEVER_RAN_DAYS_THRESHOLD = 2   # алерт если enabled но ни разу не запускался > N дней

def log(msg):
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def parse_cron_period_seconds(expr: str) -> int:
    """Грубая оценка периода cron-выражения в секундах.
    
    ВАЖНО: для кронов с ограничением по дням недели (1-5) возвращает
    максимальный интервал с учётом выходных, чтобы не давать ложных алертов.
    Основная защита — use_next_run_at в check_jobs().
    """
    parts = expr.strip().split()
    if len(parts) < 5:
        return 86400

    minute, hour, dom, mon, dow = parts[0], parts[1], parts[2], parts[3], parts[4]

    weekdays_only = dow in ('1-5',)      # Пн–Пт
    six_days = dow in ('1-6',)           # Пн–Сб

    # 1. Сначала проверяем дни недели — еженедельные задачи
    if dow not in ('*', '1-5', '1-6', '0-6'):
        # Конкретный день (1, 5, 0,6 и т.д.) = еженедельный
        return 7 * 86400  # 168 часов

    # 2. Конкретные дни месяца (28-31) = ежемесячные
    if dom not in ('*',) and '-' in dom:
        return 30 * 86400

    # 3. Каждые N минут
    if minute.startswith("*/"):
        return int(minute[2:]) * 60

    # 4. Несколько часов в день: "0 10,14,16 * * 1-5"
    if ',' in hour:
        h_ints = sorted(int(h) for h in hour.split(","))
        gaps = [h_ints[i+1] - h_ints[i] for i in range(len(h_ints)-1)]
        intra_day_gap = min(gaps) * 3600 if gaps else 86400

        if weekdays_only:
            # Пятница последний запуск → следующий Понедельник первый: ~63ч+
            # Возвращаем максимум: 3 дня * 24ч = 72ч — покрывает выходные
            weekend_gap = 3 * 86400
            return max(intra_day_gap, weekend_gap)
        elif six_days:
            # Суббота последний → следующий Понедельник: ~33ч
            weekend_gap = 2 * 86400
            return max(intra_day_gap, weekend_gap)
        return intra_day_gap

    # 5. Рабочие дни (1-5, 1-6) — один запуск в день
    if weekdays_only:
        # Пятница → Понедельник = 3 дня
        return 3 * 86400
    if six_days:
        # Суббота → Понедельник = 2 дня
        return 2 * 86400

    # 6. По умолчанию — ежедневно
    return 86400

def send_telegram_alert(message: str):
    """Отправить сообщение через openclaw message send."""
    try:
        result = subprocess.run(
            [
                "openclaw", "message", "send",
                "--channel", TELEGRAM_CHANNEL,
                "--account", "main",
                "-t", ALERT_USER_ID,
                "-m", message
            ],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and "Sent via Telegram" in result.stdout:
            return True
        log(f"  openclaw message send failed (rc={result.returncode}): {result.stderr[:300]}")
        return False
    except Exception as e:
        log(f"  send_telegram_alert error: {e}")
        return False

def check_jobs():
    if not os.path.exists(JOBS_FILE):
        log(f"❌ JOBS FILE NOT FOUND: {JOBS_FILE}")
        return

    with open(JOBS_FILE) as f:
        data = json.load(f)

    jobs = data.get("jobs", [])
    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    now_dt = datetime.now(timezone.utc)

    alerts = []
    ok_count = 0

    for job in jobs:
        if not job.get("enabled", False):
            continue

        jid = job["id"]
        name = job.get("name", "Unknown")
        agent = job.get("agentId", "?")
        schedule_expr = job.get("schedule", {}).get("expr", "")
        state = job.get("state", {})

        last_run_ms = state.get("lastRunAtMs", 0)
        last_status = state.get("lastRunStatus", "N/A")
        consecutive_errors = state.get("consecutiveErrors", 0)
        next_run_ms = state.get("nextRunAtMs", 0)

        created_ms = job.get("createdAtMs", now_ms)
        age_days = (now_ms - created_ms) / (1000 * 86400)

        issues = []

        # 1. Никогда не запускался, хотя давно создан
        if last_run_ms == 0 and age_days > NEVER_RAN_DAYS_THRESHOLD:
            issues.append(f"никогда не запускался (создан {age_days:.0f} дней назад)")

        # 2. Consecutive errors
        elif consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            issues.append(f"🔴 {consecutive_errors} ошибок подряд, последний статус: {last_status}")

        # 3. Пропуск: давно не запускался
        elif last_run_ms > 0:
            GRACE_MS = 15 * 60 * 1000  # 15 минут grace period

            if next_run_ms > 0:
                # nextRunAtMs известен — это самый точный способ проверить
                if now_ms < next_run_ms:
                    # Следующий запуск ещё не наступил — всё нормально
                    delay_min = (next_run_ms - now_ms) / 60000
                    log(f"  ⏳ SKIP  [{agent}] {name}: следующий запуск через {delay_min:.0f} мин — не алертим")
                elif now_ms < next_run_ms + GRACE_MS:
                    # В grace-периоде (15 мин после запланированного)
                    log(f"  ⏳ GRACE [{agent}] {name}: в grace-периоде после запланированного запуска")
                elif last_run_ms < next_run_ms:
                    # nextRunAtMs прошёл, а job с тех пор не запускался — реальный пропуск!
                    overdue_min = (now_ms - next_run_ms) / 60000
                    issues.append(
                        f"⏰ пропуск! Запланирован был {overdue_min:.0f} мин назад, но не запустился"
                    )
                # else: last_run >= next_run → job уже запустился после nextRunAt, всё ок
            else:
                # nextRunAtMs не задан — fallback: смотрим на тишину
                period_sec = parse_cron_period_seconds(schedule_expr)
                silence_sec = (now_ms - last_run_ms) / 1000
                max_allowed = period_sec * MAX_SILENCE_MULTIPLIER
                if silence_sec > max_allowed:
                    hours_ago = silence_sec / 3600
                    issues.append(
                        f"⏰ пропуск! Не запускался {hours_ago:.1f}ч "
                        f"(ожидалось каждые ~{period_sec/3600:.1f}ч, нет nextRunAt)"
                    )

        if issues:
            alerts.append({
                "name": name,
                "agent": agent,
                "schedule": schedule_expr,
                "issues": issues,
                "last_status": last_status
            })
            log(f"  ⚠️  ALERT [{agent}] {name}: {'; '.join(issues)}")
        else:
            ok_count += 1
            log(f"  ✅ OK    [{agent}] {name}")

    log(f"Итого: {ok_count} OK, {len(alerts)} проблем из {len(jobs)} enabled кронов")

    if alerts:
        # Загружаем историю алертов (защита от спама)
        alerted_before = {}
        if os.path.exists(ALERT_STATE_FILE):
            try:
                with open(ALERT_STATE_FILE) as sf:
                    alerted_before = json.load(sf)
            except:
                alerted_before = {}

        # Фильтруем: не алертить повторно по тому же lastRunAtMs
        new_alerts = []
        for a in alerts:
            key = a['name']
            prev_run = alerted_before.get(key, 0)
            # Находим lastRunAtMs для этого крона
            for job in jobs:
                if job.get('name') == a['name']:
                    current_run = job.get('state', {}).get('lastRunAtMs', 0)
                    if current_run != prev_run:
                        new_alerts.append(a)
                        alerted_before[key] = current_run
                    else:
                        log(f"  🔇 Пропущен повторный алерт: {a['name']} (тот же lastRun)")
                    break

        # Сохраняем state
        with open(ALERT_STATE_FILE, 'w') as sf:
            json.dump(alerted_before, sf)

        alerts = new_alerts

    if alerts:
        # Формируем сообщение алерта
        lines = ["🚨 *AXIS Cron Monitor — АЛЕРТ*\n"]
        lines.append(f"Время: {now_dt.strftime('%Y-%m-%d %H:%M')} UTC\n")
        lines.append(f"Проблемных кронов: {len(alerts)}/{len(jobs)}\n\n")
        for a in alerts:
            lines.append(f"❌ *{a['name']}* [{a['agent']}]")
            lines.append(f"   Schedule: `{a['schedule']}`")
            for issue in a['issues']:
                lines.append(f"   ⚠️ {issue}")
            lines.append("")

        lines.append("\n🔧 Действие: проверить `openclaw status` и логи кронов")
        msg = "\n".join(lines)

        log(f"Отправляю алерт в Telegram ({ALERT_USER_ID})...")
        ok = send_telegram_alert(msg)
        log(f"  Алерт отправлен: {'✅' if ok else '❌'}")
    else:
        log("✅ Все enabled кроны работают штатно — алерт не нужен")

if __name__ == "__main__":
    log("=" * 60)
    log("AXIS Cron Monitor запущен")
    check_jobs()
    log("=" * 60)
