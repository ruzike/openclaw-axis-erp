#!/usr/bin/env python3
"""
agent-monitor.py — Мониторинг нагрузки AI-агентов AXIS
Проверяет: размер SOUL.md, ошибки cron, knowledge-файлы

Запуск: python3 /home/axis/openclaw/axis-system/agent-monitor.py
"""
import json
import subprocess
from pathlib import Path
from datetime import datetime

AGENTS_DIR = Path('/home/axis/openclaw/agents')
OPENCLAW_CRON_DB = Path('/home/axis/.openclaw/cron-runs')

# Пороги нагрузки
SOUL_WARN = 200   # строк — предупреждение
SOUL_CRIT = 300   # строк — критично

AGENTS = ['main', 'ops', 'tech', 'devops', 'sales', 'hr', 'qc', 'finance', 'shket']

def check_soul(agent_id):
    soul = AGENTS_DIR / agent_id / 'SOUL.md'
    if not soul.exists():
        return None, '❓ нет файла'
    lines = len(soul.read_text(encoding='utf-8').splitlines())
    if lines >= SOUL_CRIT:
        status = f'🔴 {lines} строк (КРИТИЧНО >{SOUL_CRIT})'
    elif lines >= SOUL_WARN:
        status = f'🟡 {lines} строк (выше нормы >{SOUL_WARN})'
    else:
        status = f'✅ {lines} строк (норма)'
    return lines, status

def check_knowledge(agent_id):
    kdir = AGENTS_DIR / agent_id / 'knowledge'
    if not kdir.exists():
        return 0, '❌ нет папки'
    # Рекурсивно ищем .md файлы (включая подпапки)
    files = [f for f in kdir.rglob('*.md') if 'Zone' not in f.name]
    count = len(files)
    if count == 0:
        return 0, '❌ 0 файлов'
    return count, f'✅ {count} файлов'

def check_cron_errors():
    """Получить cron задачи со статусом error через openclaw CLI"""
    errors = []
    try:
        token = get_token()
        env = {**__import__('os').environ}
        if token:
            env['OPENCLAW_GATEWAY_TOKEN'] = token
        result = subprocess.run(
            ['openclaw', 'cron', 'list'],
            capture_output=True, text=True, timeout=10, env=env
        )
        lines = result.stdout.strip().splitlines()
        for line in lines[1:]:  # пропускаем заголовок
            # Колонка Status - ищем по позиции "error" как отдельное слово
            if '   error   ' in line or '    error   ' in line or '   error  ' in line:
                # Извлекаем название (2я колонка после UUID)
                parts = line.split()
                if len(parts) >= 2:
                    # UUID всегда 36 символов, имя идёт после
                    uuid_end = line.find(parts[0]) + len(parts[0])
                    rest = line[uuid_end:].strip()
                    # Имя задачи до расписания (cron/every)
                    for sep in ['cron ', 'every ', '  ']:
                        idx = rest.find(sep)
                        if idx > 0:
                            name = rest[:idx].strip()
                            break
                    else:
                        name = parts[1]
                    errors.append(name[:45])
    except Exception:
        pass
    return errors

def get_token():
    try:
        result = subprocess.run(
            ['openclaw', 'gateway', 'token'],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ''

def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"\n{'='*60}")
    print(f"🤖 МОНИТОРИНГ АГЕНТОВ AXIS — {now}")
    print(f"{'='*60}\n")

    warnings = []
    criticals = []

    # 1. SOUL.md нагрузка
    print("📋 SOUL.md (когнитивная нагрузка):")
    for agent_id in AGENTS:
        lines, status = check_soul(agent_id)
        print(f"  {agent_id:<10} {status}")
        if lines and lines >= SOUL_CRIT:
            criticals.append(f"{agent_id}: SOUL.md {lines} строк")
        elif lines and lines >= SOUL_WARN:
            warnings.append(f"{agent_id}: SOUL.md {lines} строк")

    # 2. Knowledge базы
    print("\n📚 Knowledge базы:")
    for agent_id in AGENTS:
        count, status = check_knowledge(agent_id)
        print(f"  {agent_id:<10} {status}")
        if count == 0:
            warnings.append(f"{agent_id}: нет knowledge файлов")

    # 3. Cron ошибки
    cron_errors = check_cron_errors()
    print("\n⏰ Cron задачи:")
    if cron_errors:
        for e in cron_errors:
            print(f"  🔴 {e}")
            criticals.append(f"Cron: {e}")
    else:
        print("  ✅ Все задачи работают")

    # 4. Итог
    print(f"\n{'='*60}")
    print("📊 ИТОГ:")
    if criticals:
        print(f"  🔴 Критично ({len(criticals)}):")
        for c in criticals:
            print(f"     • {c}")
    if warnings:
        print(f"  🟡 Предупреждения ({len(warnings)}):")
        for w in warnings:
            print(f"     • {w}")
    if not criticals and not warnings:
        print("  ✅ Система в норме")
    print(f"{'='*60}\n")

    return 1 if criticals else 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
