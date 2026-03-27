#!/usr/bin/env python3
"""Trello Automation для AXIS

Автоматизация на базе Trello API (поскольку Butler API недоступен через REST)

Функции:
1. Создание карточек из входящих задач
2. Отправка уведомлений о статусах
3. Проверка выполнения сроков
4. Создание отчётов

Использование:
    python3 trello-automation.py --action check-due-dates
    python3 trello-automation.py --action send-reminders
    python3 trello-automation.py --action generate-report
"""
import argparse
import requests
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Конфигурация
CONFIG_PATH = Path('/home/axis/openclaw/trello-config.json')
STATE_FILE = Path('/home/axis/openclaw/axis-system/trello-state.json')

# Загрузить конфиг
with open(CONFIG_PATH) as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
BOARD_ID = config['boards']['c3']['id']
MEMBERS = config['members']

def get_board_cards():
    """Получить все карточки с доски C3"""
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

def get_list_id(list_name):
    """Получить ID списка по имени"""
    lists = config['boards']['c3']['lists']
    for key, value in lists.items():
        if value['name'] == list_name:
            return value['id']
    return None

def check_due_dates():
    """Проверить сроки карточек"""
    cards = get_board_cards()

    now = datetime.now()
    due_soon = []  # Срок через 1-3 дня
    overdue = []   # Просроченные
    on_time = []   # В срок

    for card in cards:
        due_str = card.get('due')
        if not due_str:
            continue

        due_date = datetime.fromisoformat(due_str.replace('Z', '+00:00'))
        days_left = (due_date - now).days

        if days_left < 0:
            overdue.append(card)
        elif 0 <= days_left <= 3:
            due_soon.append(card)
        else:
            on_time.append(card)

    return overdue, due_soon, on_time

def send_due_reminders():
    """Отправить напоминания о сроках"""
    overdue, due_soon, on_time = check_due_dates()

    message = f"📅 Уведомление о сроках ({datetime.now().strftime('%Y-%m-%d')})\n\n"

    if overdue:
        message += f"🚨 ПРОСРОЧЕНО ({len(overdue)}):\n"
        for card in overdue:
            message += f"  • {card['name']}\n"
            message += f"    Срок: {card.get('due', 'не указан')}\n"
            message += f"    Ссылка: {card['shortUrl']}\n"

    if due_soon:
        message += f"\n⏰ Скоро истекает ({len(due_soon)}):\n"
        for card in due_soon:
            message += f"  • {card['name']}\n"
            message += f"    Срок: {card.get('due', 'не указан')}\n"
            message += f"    Ссылка: {card['shortUrl']}\n"

    if not overdue and not due_soon:
        message += "✅ Все сроки в порядке"

    # Отправить в Telegram
    print(message)

    return len(overdue) + len(due_soon)

def generate_project_report():
    """Сгенерировать отчёт по проектам"""
    cards = get_board_cards()

    lists = config['boards']['c3']['lists']
    list_names = {v['id']: v['name'] for v in lists.values()}

    report = f"""
{'='*70}
📊 ОТЧЁТ ПО ПРОЕКТАМ C3
{'='*70}
Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

    # Статистика по спискам
    for list_id, list_name in list_names.items():
        list_cards = [c for c in cards if c.get('idList') == list_id]

        report += f"📋 {list_name}: {len(list_cards)} карточек\n"

        for card in list_cards:
            due_str = card.get('due', 'не указан')
            last_activity = card.get('dateLastActivity', 'не указан')

            report += f"  • {card['name']}\n"
            report += f"    Срок: {due_str}\n"
            report += f"    Активность: {last_activity}\n"

        report += "\n"

    # Статистика по исполнителям
    employee_stats = {}

    for card in cards:
        members = card.get('idMembers', [])
        for member_id in members:
            member = MEMBERS.get(member_id)
            if member:
                name = member['username']

                if name not in employee_stats:
                    employee_stats[name] = {
                        'cards': 0,
                        'lists': set()
                    }

                employee_stats[name]['cards'] += 1
                employee_stats[name]['lists'].add(list_names.get(card.get('idList'), 'Unknown'))

    report += f"👤 Статистика по исполнителям:\n"
    for name, stats in employee_stats.items():
        report += f"  • {name}: {stats['cards']} карточек\n"
        report += f"    Списки: {', '.join(stats['lists'])}\n"

    report += f"\n{'='*70}"

    return report

def create_card_from_task(task_data):
    """Создать карточку из входящей задачи"""
    url = 'https://api.trello.com/1/cards'
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'idList': task_data.get('list_id', get_list_id('backlog')),
        'name': task_data.get('name', 'Новая задача'),
        'desc': task_data.get('description', ''),
        'due': task_data.get('due', ''),
        'pos': 'top'
    }

    r = requests.post(url, params=params)
    if r.status_code == 200:
        return r.json()
    return None

def main():
    parser = argparse.ArgumentParser(description='Trello Automation для AXIS')
    parser.add_argument('--action', choices=['check-due-dates', 'send-reminders', 'generate-report', 'create-card'],
                        help='Действие')
    parser.add_argument('--list', help='Название списка для карточки')
    parser.add_argument('--name', help='Название карточки')
    parser.add_argument('--desc', help='Описание карточки')
    parser.add_argument('--due', help='Срок (YYYY-MM-DD)')

    args = parser.parse_args()

    if args.action == 'check-due-dates':
        overdue, due_soon, on_time = check_due_dates()
        print(f"📊 Сроки карточек:")
        print(f"  🚨 Просрочено: {len(overdue)}")
        print(f"  ⏰ Скоро истекает: {len(due_soon)}")
        print(f"  ✅ В срок: {len(on_time)}")

    elif args.action == 'send-reminders':
        count = send_due_reminders()
        print(f"\n📤 Отправлено напоминаний: {count}")

    elif args.action == 'generate-report':
        report = generate_project_report()
        print(report)

    elif args.action == 'create-card':
        list_id = get_list_id(args.list) if args.list else None
        task_data = {
            'list_id': list_id,
            'name': args.name,
            'description': args.desc,
            'due': args.due
        }

        card = create_card_from_task(task_data)
        if card:
            print(f"✅ Карточка создана: {card['shortUrl']}")
        else:
            print("❌ Ошибка создания карточки")
            sys.exit(1)

    return 0

if __name__ == '__main__':
    sys.exit(main())
