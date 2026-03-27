#!/usr/bin/env python3
"""Team Report - Сбор и обработка отчётов команды"""
import json
import sys
from datetime import datetime
from pathlib import Path

STATE_PATH = Path('/home/axis/openclaw/team-state.json')

def load_state():
    """Загрузить состояние"""
    if STATE_PATH.exists():
        with open(STATE_PATH, 'r') as f:
            return json.load(f)
    return {"employees": {}, "escalations": [], "daily_reports": {}}

def save_state(state):
    """Сохранить состояние"""
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def save_report(employee_id, report_text):
    """Сохранить отчёт сотрудника"""
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    
    if today not in state['daily_reports']:
        state['daily_reports'][today] = {}
    
    state['daily_reports'][today][employee_id] = {
        'timestamp': datetime.now().isoformat(),
        'text': report_text,
        'employee': state['employees'].get(employee_id, {}).get('name', 'Unknown')
    }
    
    # Обновить last_response
    if employee_id in state['employees']:
        state['employees'][employee_id]['last_response'] = datetime.now().isoformat()
        state['employees'][employee_id]['status'] = 'reported'
    
    save_state(state)
    print(f"✅ Отчёт сохранён: {state['employees'][employee_id]['name']}")
    return True

def get_daily_report(date=None):
    """Получить отчёт за день"""
    state = load_state()
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    reports = state['daily_reports'].get(date, {})
    if not reports:
        print(f"📊 Нет отчётов за {date}")
        return
    
    print(f"📊 Отчёты команды за {date}:\n")
    for emp_id, report in reports.items():
        employee = report['employee']
        text = report['text']
        time = datetime.fromisoformat(report['timestamp']).strftime('%H:%M')
        print(f"👤 {employee} ({time}):")
        print(f"{text}\n")

def check_missing_reports():
    """Проверить, кто не сдал отчёт"""
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    reports = state['daily_reports'].get(today, {})
    
    missing = []
    for emp_id, emp_data in state['employees'].items():
        if emp_id not in reports:
            missing.append(emp_data['name'])
    
    if missing:
        print(f"⚠️ Не сдали отчёт: {', '.join(missing)}")
        return missing
    else:
        print("✅ Все отчёты получены")
        return []

def generate_summary():
    """Сгенерировать сводку для Руслана"""
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    reports = state['daily_reports'].get(today, {})
    
    summary = f"📊 Итоги команды за {today}\n\n"
    
    if not reports:
        summary += "Нет отчётов\n"
    else:
        for emp_id, report in reports.items():
            employee = report['employee']
            summary += f"👤 {employee}:\n{report['text']}\n\n"
    
    # Добавить эскалации
    escalations = state.get('escalations', [])
    if escalations:
        summary += "\n🚨 Эскалации:\n"
        for esc in escalations:
            summary += f"  • {esc['message']}\n"
    
    print(summary)
    return summary

def process_message(employee_id, message_text):
    """Обработать сообщение от сотрудника (для интеграции с агентом)"""
    state = load_state()
    
    # Обновить last_response
    if employee_id in state['employees']:
        state['employees'][employee_id]['last_response'] = datetime.now().isoformat()
        save_state(state)
    
    # Проверить, это отчёт или обычное сообщение
    # (упрощённо: если после вечернего пинга - это отчёт)
    emp_data = state['employees'].get(employee_id, {})
    last_evening = emp_data.get('last_evening_ping')
    
    if last_evening:
        last_evening_dt = datetime.fromisoformat(last_evening)
        if (datetime.now() - last_evening_dt).seconds < 7200:  # 2 часа
            # Это вероятно отчёт
            save_report(employee_id, message_text)
            return "report_saved"
    
    return "message_received"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование:")
        print("  team-report.py save <emp_id> <text>  - сохранить отчёт")
        print("  team-report.py show [date]           - показать отчёты")
        print("  team-report.py missing               - кто не сдал отчёт")
        print("  team-report.py summary               - сводка для Руслана")
        print("  team-report.py process <emp_id> <text> - обработать сообщение")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'save':
        if len(sys.argv) < 4:
            print("❌ Укажите ID и текст отчёта")
            sys.exit(1)
        emp_id = sys.argv[2]
        text = ' '.join(sys.argv[3:])
        save_report(emp_id, text)
    
    elif command == 'show':
        date = sys.argv[2] if len(sys.argv) > 2 else None
        get_daily_report(date)
    
    elif command == 'missing':
        check_missing_reports()
    
    elif command == 'summary':
        generate_summary()
    
    elif command == 'process':
        if len(sys.argv) < 4:
            print("❌ Укажите ID и текст")
            sys.exit(1)
        emp_id = sys.argv[2]
        text = ' '.join(sys.argv[3:])
        result = process_message(emp_id, text)
        print(f"✅ {result}")
    
    else:
        print(f"❌ Неизвестная команда: {command}")
