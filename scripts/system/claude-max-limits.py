#!/usr/bin/env python3
"""
Claude Max Subscription Limits Checker
Проверяет лимиты подписки Claude Max через claude.ai API.
Usage: python3 claude-max-limits.py [--json]
"""

import json
import subprocess
import sys
import os
from datetime import datetime, timezone

CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def api_request(session_key, path):
    """Делает запрос к claude.ai API через curl (обходит Cloudflare)."""
    url = f"https://claude.ai{path}"
    result = subprocess.run([
        'curl', '-s', '-o', '-', '-w', '\n%{http_code}',
        '--http2', '--tlsv1.3',
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        '-H', 'Accept: application/json',
        '-H', f'Cookie: sessionKey={session_key}',
        '-H', 'Referer: https://claude.ai/chats',
        '-H', 'Sec-Fetch-Dest: empty',
        '-H', 'Sec-Fetch-Mode: cors',
        '-H', 'Sec-Fetch-Site: same-origin',
        url
    ], capture_output=True, text=True, timeout=15)

    lines = result.stdout.strip().split('\n')
    code = int(lines[-1]) if lines else 0
    body = '\n'.join(lines[:-1])

    if code == 200 and body:
        return json.loads(body)
    return None

def get_org_uuid(session_key):
    """Получить UUID организации."""
    data = api_request(session_key, '/api/organizations')
    if data and isinstance(data, list) and len(data) > 0:
        return data[0].get('uuid'), data[0].get('name', 'Unknown')
    return None, None

def get_usage(session_key, org_uuid):
    """Получить данные об использовании лимитов."""
    return api_request(session_key, f'/api/organizations/{org_uuid}/usage')

def progress_bar(pct, width=12):
    """Создать прогресс-бар."""
    pct = min(100, max(0, pct))
    filled = round(width * pct / 100)
    return '█' * filled + '░' * (width - filled)

def format_reset(reset_str):
    """Форматировать время до сброса."""
    if not reset_str:
        return "неизвестно"
    try:
        reset_dt = datetime.fromisoformat(reset_str)
        if reset_dt.tzinfo is None:
            reset_dt = reset_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = reset_dt - now
        secs = int(diff.total_seconds())

        if secs <= 0:
            return "скоро"
        if secs < 60:
            return f"{secs}сек"
        mins = secs // 60
        if mins < 60:
            return f"{mins}мин"
        hours = mins // 60
        mins_left = mins % 60
        if hours < 24:
            return f"{hours}ч {mins_left}мин"
        days = hours // 24
        hours_left = hours % 24
        return f"{days}д {hours_left}ч"
    except Exception:
        return reset_str[:16]

def status_emoji(pct):
    if pct >= 90:
        return "🔴"
    if pct >= 70:
        return "⚠️"
    return "✅"

def format_output(usage, org_name):
    """Форматировать красивый вывод."""
    lines = [f"🤖 **Claude Max Limits** ({org_name})", ""]

    # Session (5-hour window)
    if "five_hour" in usage and usage["five_hour"]:
        fh = usage["five_hour"]
        pct = round(fh.get("utilization", 0))
        reset = format_reset(fh.get("resets_at"))
        bar = progress_bar(pct)
        emoji = status_emoji(pct)
        lines.append(f"Session 5h (сброс: {reset})")
        lines.append(f"{bar} {pct}% {emoji}")
        lines.append("")

    # Weekly (7-day window)
    if "seven_day" in usage and usage["seven_day"]:
        sd = usage["seven_day"]
        pct = round(sd.get("utilization", 0))
        reset = format_reset(sd.get("resets_at"))
        bar = progress_bar(pct)
        emoji = status_emoji(pct)
        lines.append(f"Week — All models (сброс: {reset})")
        lines.append(f"{bar} {pct}% {emoji}")
        lines.append("")

    # Opus (7-day per-model)
    if "seven_day_opus" in usage and usage["seven_day_opus"]:
        op = usage["seven_day_opus"]
        pct = round(op.get("utilization", 0))
        reset = format_reset(op.get("resets_at"))
        bar = progress_bar(pct)
        emoji = status_emoji(pct)
        lines.append(f"Opus (сброс: {reset})")
        lines.append(f"{bar} {pct}% {emoji}")
        lines.append("")

    # Sonnet (7-day per-model)
    if "seven_day_sonnet" in usage and usage["seven_day_sonnet"]:
        sn = usage["seven_day_sonnet"]
        pct = round(sn.get("utilization", 0))
        reset = format_reset(sn.get("resets_at"))
        bar = progress_bar(pct)
        emoji = status_emoji(pct)
        lines.append(f"Sonnet (сброс: {reset})")
        lines.append(f"{bar} {pct}% {emoji}")
        lines.append("")

    # Cowork
    if "seven_day_cowork" in usage and usage["seven_day_cowork"]:
        cw = usage["seven_day_cowork"]
        pct = round(cw.get("utilization", 0))
        reset = format_reset(cw.get("resets_at"))
        bar = progress_bar(pct)
        emoji = status_emoji(pct)
        lines.append(f"Claude Code (сброс: {reset})")
        lines.append(f"{bar} {pct}% {emoji}")
        lines.append("")

    # Extra usage
    if "extra_usage" in usage and usage["extra_usage"]:
        eu = usage["extra_usage"]
        used = eu.get("amount_used", 0)
        limit = eu.get("limit", 0)
        lines.append(f"Extra usage: ${used:.2f} / ${limit:.2f} лимит")
        lines.append("")

    # Overall status
    max_pct = 0
    for key in ("five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet"):
        if key in usage and usage[key]:
            max_pct = max(max_pct, usage[key].get("utilization", 0))

    if max_pct >= 95:
        lines.append("🔴 Лимиты исчерпаны! Подождите сброса.")
    elif max_pct >= 70:
        lines.append("⚠️ Лимиты выше 70%, используйте экономно")
    else:
        lines.append("✅ Всё ок, запас есть")

    return "\n".join(lines)

def main():
    json_mode = "--json" in sys.argv
    config = load_config()
    session_key = config["env"]["CLAUDE_WEB_SESSION_KEY"]

    # Get org
    org_uuid, org_name = get_org_uuid(session_key)
    if not org_uuid:
        print("❌ Не удалось получить организацию. Session key может быть просрочен.")
        sys.exit(1)

    # Get usage
    usage = get_usage(session_key, org_uuid)
    if not usage:
        print("❌ Не удалось получить данные об использовании.")
        sys.exit(1)

    if json_mode:
        print(json.dumps(usage, indent=2, ensure_ascii=False))
    else:
        print(format_output(usage, org_name))

if __name__ == "__main__":
    main()
