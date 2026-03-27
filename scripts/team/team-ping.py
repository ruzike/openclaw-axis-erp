#!/usr/bin/env python3
"""Team Ping - Автоматические пинги сотрудникам (без Custom Fields)"""
import json
import sys
import requests
from datetime import datetime
from pathlib import Path

# Загрузка конфигов
CONFIG_PATH = Path('/home/axis/openclaw/trello-config.json')
with open(CONFIG_PATH, 'r') as f:
    trello_config = json.load(f)

API_KEY = trello_config['api']['key']
TOKEN = trello_config['api']['token']
BOARD_ID = trello_config['boards']['production']['id']
C3_BOARD_ID = trello_config['boards']['c3']['id']

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

def get_board_cards():
    """Получить все карточки с доски Production и C3"""
    cards = []
    
    # Сначала Production
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/cards"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'members': 'true',
        'member_fields': 'fullName,username',
        'fields': 'name,idList,idMembers,labels,due,dateLastActivity'
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        cards.extend(r.json())
        
    # Затем C3
    url_c3 = f"https://api.trello.com/1/boards/{C3_BOARD_ID}/cards"
    r_c3 = requests.get(url_c3, params=params)
    if r_c3.status_code == 200:
        for card in r_c3.json():
            card['name'] = f"[C3] {card['name']}"
            cards.append(card)
            
    return cards

def get_board_members():
    """Получить всех участников доски"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/members"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'fields': 'id,fullName,username'
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return r.json()
    return []

def get_member_id_by_name(name):
    """Получить Trello member ID по имени сотрудника"""
    members = get_board_members()
    for member in members:
        if name.lower() in member.get('fullName', '').lower() or name.lower() in member.get('username', '').lower():
            return member['id']
    return None

def get_employee_tasks(employee_id):
    """Получить задачи сотрудника по Telegram ID"""
    cards = get_board_cards()
    state = load_state()
    
    employee_name = state['employees'].get(employee_id, {}).get('name', '')
    if not employee_name:
        return []
    
    # Получить Trello member ID
    
    # 1. Сначала пробуем найти через конфиг (надёжнее)
    trello_member_id = None
    if 'members' in trello_config:
        for key, val in trello_config['members'].items():
            if str(val.get('telegram_id')) == str(employee_id):
                trello_member_id = val.get('trello_id')
                break

    # 2. Если не нашли в конфиге, ищем по имени (fallback)
    if not trello_member_id:
        trello_member_id = get_member_id_by_name(employee_name)
    
    if not trello_member_id:
        return []
        
    return filter_tasks_by_member(cards, trello_member_id)

def filter_tasks_by_member(cards, trello_member_id):
    employee_cards = []
    for card in cards:
        # Пропустить завершённые
        if card.get('idList') == trello_config['boards']['production']['lists']['done']['id']:
            continue
        
        if trello_member_id in card.get('idMembers', []):
            employee_cards.append(card)
    
    return employee_cards

def get_card_priority(card):
    """Получить приоритет карточки из labels"""
    labels = card.get('labels', [])
    for label in labels:
        name = label.get('name', '')
        if '🔴' in name or 'Critical' in name:
            return 'critical'
        elif '🟠' in name or 'High' in name:
            return 'high'
        elif '🟡' in name or 'Medium' in name:
            return 'medium'
        elif '🟢' in name or 'Low' in name:
            return 'low'
    return 'normal'

def format_tasks_by_priority(tasks):
    """Отформатировать задачи по приоритетам"""
    critical = []
    high = []
    normal = []
    
    for task in tasks:
        priority = get_card_priority(task)
        
        if priority == 'critical':
            critical.append(task['name'])
        elif priority == 'high':
            high.append(task['name'])
        else:
            normal.append(task['name'])
    
    return critical, high, normal

def morning_ping_message(employee_id):
    """Создать утреннее сообщение"""
    state = load_state()
    employee_name = state['employees'].get(employee_id, {}).get('name', 'Коллега')
    
    tasks = get_employee_tasks(employee_id)
    
    if not tasks:
        return f"Доброе утро, {employee_name}! 👋\n\nНа сегодня задач нет. Свяжись с Русланом за новыми задачами."
    
    critical, high, normal = format_tasks_by_priority(tasks)
    
    message = f"Доброе утро, {employee_name}! 👋\n\nТвои задачи на сегодня:\n"
    
    if critical:
        message += "\n🔴 Critical:\n"
        for task in critical:
            message += f"  • {task}\n"
    
    if high:
        message += "\n🟠 High:\n"
        for task in high:
            message += f"  • {task}\n"
    
    if normal:
        message += "\n🟡 Обычные:\n"
        for task in normal:
            message += f"  • {task}\n"
    
    message += "\nНапиши когда начнёшь работу."
    
    # Обновить время последнего пинга
    state['employees'][employee_id]['last_morning_ping'] = datetime.now().isoformat()
    save_state(state)
    
    return message

def afternoon_check_message(employee_id):
    """Дневная проверка прогресса"""
    state = load_state()
    employee_name = state['employees'].get(employee_id, {}).get('name', 'Коллега')
    
    # Проверить: отвечал ли после утреннего пинга
    last_response = state['employees'][employee_id].get('last_response')
    last_morning_ping = state['employees'][employee_id].get('last_morning_ping')
    
    if not last_response or (last_morning_ping and last_response < last_morning_ping):
        tasks = get_employee_tasks(employee_id)
        if tasks:
            task_name = tasks[0]['name']
            return f"Привет! Как прогресс по '{task_name}'? Нужна помощь?"
    
    # Обновить время последнего пинга
    state['employees'][employee_id]['last_afternoon_ping'] = datetime.now().isoformat()
    save_state(state)
    
    return None

def evening_report_message(employee_id):
    """Запрос вечернего отчёта"""
    state = load_state()
    employee_name = state['employees'].get(employee_id, {}).get('name', 'Коллега')
    
    message = f"Привет! Время подвести итоги дня:\n\n"
    message += "• Что сделал?\n"
    message += "• Что не успел и почему?\n"
    message += "• План на завтра?"
    
    # Обновить время последнего пинга
    state['employees'][employee_id]['last_evening_ping'] = datetime.now().isoformat()
    save_state(state)
    
    return message

def send_telegram_message(telegram_id, message):
    """Вывести сообщение для отправки (используется team-bridge.py)"""
    print(message)
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование:")
        print("  team-ping.py morning <emp_id>    - утренний пинг")
        print("  team-ping.py afternoon <emp_id>  - дневная проверка")
        print("  team-ping.py evening <emp_id>    - вечерний отчёт")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'morning':
        if len(sys.argv) < 3:
            print("❌ Укажите ID сотрудника", file=sys.stderr)
            sys.exit(1)
        emp_id = sys.argv[2]
        message = morning_ping_message(emp_id)
        send_telegram_message(emp_id, message)
    
    elif command == 'afternoon':
        if len(sys.argv) < 3:
            print("❌ Укажите ID сотрудника", file=sys.stderr)
            sys.exit(1)
        emp_id = sys.argv[2]
        message = afternoon_check_message(emp_id)
        if message:
            send_telegram_message(emp_id, message)
        else:
            state = load_state()
            employee_name = state['employees'].get(emp_id, {}).get('name', emp_id)
            print(f"✓ {employee_name}: ответил после утреннего пинга, проверка не требуется", file=sys.stderr)
    
    elif command == 'evening':
        if len(sys.argv) < 3:
            print("❌ Укажите ID сотрудника", file=sys.stderr)
            sys.exit(1)
        emp_id = sys.argv[2]
        message = evening_report_message(emp_id)
        send_telegram_message(emp_id, message)
    
    else:
        print(f"❌ Неизвестная команда: {command}", file=sys.stderr)
        sys.exit(1)
