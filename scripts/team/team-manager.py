#!/usr/bin/env python3
"""Team Manager - Основной менеджер команды (без платных Custom Fields)"""
import json
import requests
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Пути
CONFIG_PATH = Path('/home/axis/openclaw/trello-config.json')
STATE_PATH = Path('/home/axis/openclaw/team-state.json')

# Загрузка конфигов
with open(CONFIG_PATH, 'r') as f:
    trello_config = json.load(f)

API_KEY = trello_config['api']['key']
TOKEN = trello_config['api']['token']
BOARD_ID = trello_config['boards']['production']['id']

# Mapping сотрудников: Telegram ID → имя
EMPLOYEES = {
    'MEMBER1_TELEGRAM_ID': {'name': 'Мирас', 'username': '@MIKA721S'},
    'MEMBER2_TELEGRAM_ID': {'name': 'Бахытжан', 'username': '@Sagimbayev'}
}

def load_state():
    """Загрузить состояние команды"""
    if STATE_PATH.exists():
        with open(STATE_PATH, 'r') as f:
            return json.load(f)
    return {"employees": {}, "escalations": [], "daily_reports": {}}

def save_state(state):
    """Сохранить состояние команды"""
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_board_cards():
    """Получить все карточки с доски Production (с members и labels)"""
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
        return r.json()
    return []

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

def get_board_labels():
    """Получить все метки доски"""
    url = f"https://api.trello.com/1/boards/{BOARD_ID}/labels"
    params = {'key': API_KEY, 'token': TOKEN}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return r.json()
    return []

def create_label(name, color):
    """Создать метку на доске"""
    url = "https://api.trello.com/1/labels"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'name': name,
        'color': color,
        'idBoard': BOARD_ID
    }
    r = requests.post(url, params=params)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"❌ Ошибка создания метки {name}: {r.text}")
        return None

def setup_priority_labels():
    """Настроить метки приоритетов"""
    existing_labels = get_board_labels()
    existing_names = {label['name'] for label in existing_labels}
    
    print("🏷️ Настройка меток приоритетов...")
    
    priorities = [
        ('🔴 Critical', 'red'),
        ('🟠 High', 'orange'),
        ('🟡 Medium', 'yellow'),
        ('🟢 Low', 'green')
    ]
    
    for name, color in priorities:
        if name not in existing_names:
            create_label(name, color)
            print(f"  ✅ Создана метка '{name}'")
        else:
            print(f"  ✓ Метка '{name}' уже существует")
    
    print("✅ Метки приоритетов настроены")

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
    trello_member_id = get_member_id_by_name(employee_name)
    if not trello_member_id:
        return []
    
    # Фильтр задач по исполнителю (idMembers)
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

def check_task_triggers():
    """Проверить триггеры по задачам"""
    cards = get_board_cards()
    state = load_state()
    now = datetime.now().astimezone()
    
    triggers = []
    
    for card in cards:
        # Пропустить завершённые
        if card.get('idList') == trello_config['boards']['production']['lists']['done']['id']:
            continue
        
        # Проверка: задача в работе > 2 дней
        if card.get('idList') == trello_config['boards']['production']['lists']['inProgress']['id']:
            last_activity = datetime.fromisoformat(card['dateLastActivity'].replace('Z', '+00:00'))
            if (now - last_activity).days > 2:
                triggers.append({
                    'type': 'stuck_task',
                    'card': card,
                    'message': f"Задача '{card['name']}' в работе больше 2 дней. Что блокирует?"
                })
        
        # Проверка дедлайна (due date)
        due_str = card.get('due')
        if due_str:
            due = datetime.fromisoformat(due_str.replace('Z', '+00:00'))
            hours_left = (due - now).total_seconds() / 3600
            
            if hours_left < 0:
                triggers.append({
                    'type': 'deadline_overdue',
                    'card': card,
                    'message': f"🚨 Дедлайн просрочен: '{card['name']}'",
                    'escalate': True
                })
            elif 0 < hours_left < 24:
                triggers.append({
                    'type': 'deadline_warning',
                    'card': card,
                    'message': f"⚠️ Дедлайн через {int(hours_left)}ч: '{card['name']}'"
                })
    
    return triggers

def check_employee_silence():
    """Проверить молчание сотрудников"""
    state = load_state()
    now = datetime.now()
    alerts = []
    
    for emp_id, emp_data in state['employees'].items():
        last_response = emp_data.get('last_response')
        if not last_response:
            continue
        
        last_time = datetime.fromisoformat(last_response)
        hours_silent = (now - last_time).total_seconds() / 3600
        
        # Проверка только в рабочее время (10:00-18:00)
        if 10 <= now.hour <= 18:
            if hours_silent > 4:
                alerts.append({
                    'type': 'employee_silent',
                    'employee_id': emp_id,
                    'hours': int(hours_silent),
                    'message': f"{emp_data['name']} не отвечает {int(hours_silent)}ч"
                })
            
            if hours_silent > 6:
                alerts.append({
                    'type': 'employee_silent_critical',
                    'employee_id': emp_id,
                    'hours': int(hours_silent),
                    'message': f"🚨 {emp_data['name']} не отвечает {int(hours_silent)}ч",
                    'escalate': True
                })
    
    return alerts

def update_employee_status(employee_id, status, message=None):
    """Обновить статус сотрудника"""
    state = load_state()
    if employee_id in state['employees']:
        state['employees'][employee_id]['status'] = status
        state['employees'][employee_id]['last_response'] = datetime.now().isoformat()
        if message:
            state['employees'][employee_id]['last_message'] = message
        save_state(state)
        return True
    return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование:")
        print("  team-manager.py setup          - настроить метки приоритетов")
        print("  team-manager.py tasks <emp_id> - показать задачи сотрудника")
        print("  team-manager.py triggers       - проверить триггеры")
        print("  team-manager.py silence        - проверить молчание")
        print("  team-manager.py status <emp_id> <status> - обновить статус")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'setup':
        setup_priority_labels()
    
    elif command == 'tasks':
        if len(sys.argv) < 3:
            print("❌ Укажите ID сотрудника")
            sys.exit(1)
        emp_id = sys.argv[2]
        tasks = get_employee_tasks(emp_id)
        print(f"📋 Задачи сотрудника {emp_id}:")
        for task in tasks:
            priority = get_card_priority(task)
            due = task.get('due')
            due_str = f" (⏰ {due[:10]})" if due else ""
            print(f"  • [{priority}] {task['name']}{due_str}")
    
    elif command == 'triggers':
        triggers = check_task_triggers()
        print(f"🔔 Найдено триггеров: {len(triggers)}")
        for t in triggers:
            print(f"  {t['type']}: {t['message']}")
    
    elif command == 'silence':
        alerts = check_employee_silence()
        print(f"🔕 Проверка молчания: {len(alerts)}")
        for a in alerts:
            print(f"  {a['type']}: {a['message']}")
    
    elif command == 'status':
        if len(sys.argv) < 4:
            print("❌ Укажите ID и статус")
            sys.exit(1)
        emp_id = sys.argv[2]
        status = sys.argv[3]
        if update_employee_status(emp_id, status):
            print(f"✅ Статус обновлён: {emp_id} -> {status}")
        else:
            print("❌ Сотрудник не найден")
