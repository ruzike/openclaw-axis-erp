#!/usr/bin/env python3
"""Добавление карточки 'Информационные доски ЖК Давинчи комфорт'"""
import json
import requests

# Загружаем конфиг
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

# Получаем ID доски и списка "Очередь"
board_config = config['boards']['ced_supervision']
list_id = board_config['lists']['backlog']['id']

# Создаём карточку
print("🎯 Создаю карточку 'Информационные доски ЖК Давинчи комфорт'...")
url = "https://api.trello.com/1/cards"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'idList': list_id,
    'name': 'Информационные доски ЖК Давинчи комфорт'
}
r = requests.post(url, params=params)
if r.status_code != 200:
    print(f"❌ Ошибка создания карточки: {r.text}")
    exit(1)

card = r.json()
card_id = card['id']
print(f"✅ Карточка создана: {card['shortUrl']}")

# Добавляем чеклист с подзадачами
print("\n☑️  Создаю чеклист...")
url = "https://api.trello.com/1/checklists"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'idCard': card_id,
    'name': 'Подзадачи'
}
r = requests.post(url, params=params)
if r.status_code != 200:
    print(f"❌ Ошибка создания чеклиста: {r.text}")
    exit(1)

checklist = r.json()
checklist_id = checklist['id']

# Добавляем пункты чеклиста
tasks = [
    "Разработать",
    "Получить счет",
    "Оплатить",
    "Получить",
    "Смонтировать"
]

for task in tasks:
    url = f"https://api.trello.com/1/checklists/{checklist_id}/checkItems"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'name': task
    }
    r = requests.post(url, params=params)
    if r.status_code == 200:
        print(f"  ✅ {task}")
    else:
        print(f"  ❌ {task}: {r.text}")

print(f"\n🎉 Готово! Карточка: {card['shortUrl']}")
