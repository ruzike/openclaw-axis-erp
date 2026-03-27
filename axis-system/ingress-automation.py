#!/usr/bin/env python3
"""Автоматизация входящих задач → Trello C3

Слушает входящие задачи (Telegram, email, другие источники) и создаёт карточки на доске C3

Источники:
1. Telegram команды (определяются по ключевым словам)
2. Email (будет добавлен позже)
3. API (будет добавлен позже)
"""
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

# Конфигурация
CONFIG_PATH = Path('/home/axis/openclaw/trello-config.json')
INGRESS_FILE = Path('/home/axis/openclaw/axis-system/ingress-tasks.json')
STATE_FILE = Path('/home/axis/openclaw/axis-system/ingress-state.json')

# Загрузить конфиг
with open(CONFIG_PATH) as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
BOARD_ID = config['boards']['c3']['id']
MEMBERS = config['members']

def load_ingress_tasks():
    """Загрузить входящие задачи"""
    if INGRESS_FILE.exists():
        with open(INGRESS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_ingress_tasks(tasks):
    """Сохранить входящие задачи"""
    with open(INGRESS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

def load_state():
    """Загрузить состояние"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'processed': [], 'failed': []}

def save_state(state):
    """Сохранить состояние"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def create_card_from_task(task):
    """Создать карточку из задачи"""
    url = 'https://api.trello.com/1/cards'
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'idList': task.get('list_id', get_list_id('backlog')),
        'name': task.get('name', 'Новая задача'),
        'desc': task.get('description', ''),
        'due': task.get('due', ''),
        'pos': 'top'
    }

    r = requests.post(url, params=params)
    if r.status_code == 200:
        return r.json()
    return None

def get_list_id(list_name):
    """Получить ID списка по имени"""
    lists = config['boards']['c3']['lists']
    for key, value in lists.items():
        if value['name'] == list_name:
            return value['id']
    return None

def process_task(task):
    """Обработать входящую задачу"""
    # Создать карточку
    card = create_card_from_task(task)

    if card:
        return {
            'status': 'success',
            'card_id': card['id'],
            'card_url': card['shortUrl']
        }
    else:
        return {
            'status': 'failed',
            'error': 'Ошибка создания карточки'
        }

def parse_telegram_message(message):
    """Распарсить сообщение из Telegram"""
    # Формат: /create <type> <name> <executor> <deadline>
    if message.startswith('/create '):
        parts = message[8:].strip().split()
        if len(parts) >= 4:
            return {
                'type': parts[0],
                'name': parts[1],
                'executor': parts[2],
                'deadline': parts[3] if len(parts) > 3 else None
            }
    return None

def main():
    """Главная функция"""
    import requests

    # Загрузить задачи
    tasks = load_ingress_tasks()
    state = load_state()

    if not tasks:
        print("📭 Входящих задач нет")
        return 0

    print(f"📥 Обработка {len(tasks)} входящих задач...")

    processed_count = 0
    failed_count = 0

    for i, task in enumerate(tasks):
        # Пропустить уже обработанные
        if task.get('id') in state['processed']:
            continue

        print(f"\n[{i+1}/{len(tasks)}] Обработка: {task.get('name', 'без названия')}")

        # Создать карточку
        result = process_task(task)

        if result['status'] == 'success':
            print(f"✅ Карточка создана: {result['card_url']}")
            processed_count += 1
            state['processed'].append(task.get('id'))
        else:
            print(f"❌ Ошибка: {result['error']}")
            failed_count += 1
            state['failed'].append(task.get('id'))

    # Сохранить состояние
    save_state(state)

    # Удалить обработанные задачи
    remaining_tasks = [t for t in tasks if t.get('id') not in state['processed']]
    save_ingress_tasks(remaining_tasks)

    print(f"\n{'='*60}")
    print(f"✅ Обработано: {processed_count}")
    print(f"❌ Ошибок: {failed_count}")
    print(f"{'='*60}")

    return failed_count

if __name__ == '__main__':
    sys.exit(main())
