#!/usr/bin/env python3
"""Team Bridge - Мост между скриптами команды и Telegram через агента"""
import subprocess
import sys

def send_via_agent(target_id, message):
    """Отправить сообщение через агента OpenClaw"""
    # Формируем команду для агента
    cmd = [
        'openclaw', 'message', 'send',
        '--channel', 'telegram',
        '--account', 'ops',
        '--target', str(target_id),
        '--message', message
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True
        else:
            print(f"❌ Ошибка отправки: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        return False

def process_ping_output(output):
    """Обработать вывод team-ping.py и отправить сообщения"""
    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('SEND_MESSAGE|'):
            # Формат: SEND_MESSAGE|<target_id>|<message>
            parts = line.split('|', 2)
            if len(parts) == 3:
                _, target_id, message = parts
                print(f"📤 Отправка {target_id}: {message[:50]}...")
                send_via_agent(target_id, message)
        
        elif line.startswith('ESCALATE|'):
            # Формат: ESCALATE|<ruslan_id>|<message>
            parts = line.split('|', 2)
            if len(parts) == 3:
                _, target_id, message = parts
                escalation_msg = f"🚨 ЭСКАЛАЦИЯ\n\n{message}"
                print(f"🚨 Эскалация Руслану: {message[:50]}...")
                send_via_agent(target_id, escalation_msg)
        
        elif line.startswith('BROADCAST|'):
            # Формат: BROADCAST|<message>
            # Отправить всем сотрудникам
            message = line.split('|', 1)[1]
            print(f"📢 Broadcast: {message[:50]}...")
            # Отправим обоим сотрудникам
            send_via_agent('MEMBER1_TELEGRAM_ID', message)  # Мирас
            send_via_agent('MEMBER2_TELEGRAM_ID', message)  # Бахытжан
        
        else:
            # Обычный вывод
            print(line)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование:")
        print("  team-bridge.py morning    - утренний пинг")
        print("  team-bridge.py afternoon  - дневная проверка")
        print("  team-bridge.py evening    - вечерний отчёт")
        print("  team-bridge.py check      - проверка триггеров")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # ID сотрудников
    EMPLOYEES = {
        'MEMBER1_TELEGRAM_ID': 'Мирас',
        'MEMBER2_TELEGRAM_ID': 'Бахытжан'
    }
    
    # Запустить соответствующий скрипт для каждого сотрудника
    try:
        for emp_id, emp_name in EMPLOYEES.items():
            print(f"🔄 {emp_name} (ID: {emp_id})...", end=" ", flush=True)
            
            result = subprocess.run(
                ['python3', '/home/axis/openclaw/scripts/team/team-ping.py', command, emp_id],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Обработать вывод
            if result.stdout:
                # Если это сообщение для отправки
                message = result.stdout.strip()
                if message:
                    print(f"📤 Отправка")
                    send_via_agent(emp_id, message)
            
            # Вывести статус из stderr (если есть)
            if result.stderr:
                print(result.stderr.strip())
    
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)
