#!/usr/bin/env python3
"""Создание доски СЭД Акторский надзор"""
import json
import requests

# Загружаем конфиг
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

# 1. Создаём доску
print("📋 Создаю доску 'СЭД Акторский надзор'...")
url = "https://api.trello.com/1/boards"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'name': 'СЭД Акторский надзор',
    'defaultLists': 'false'  # Не создавать дефолтные колонки
}
r = requests.post(url, params=params)
if r.status_code != 200:
    print(f"❌ Ошибка создания доски: {r.text}")
    exit(1)

board = r.json()
board_id = board['id']
board_url = board['shortUrl']
print(f"✅ Доска создана: {board_url}")

# 2. Создаём колонки
lists = [
    "Очередь",
    "В работе", 
    "На оплате",
    "На монтаже",
    "Готово",
    "Не актуально"
]

list_ids = {}
print("\n📝 Создаю колонки...")
for list_name in lists:
    url = "https://api.trello.com/1/lists"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'name': list_name,
        'idBoard': board_id
    }
    r = requests.post(url, params=params)
    if r.status_code == 200:
        list_data = r.json()
        list_ids[list_name] = list_data['id']
        print(f"  ✅ {list_name}")
    else:
        print(f"  ❌ {list_name}: {r.text}")

# 3. Создаём карточку "Почтовые ящики ЖК Давинчи комфорт"
print("\n🎯 Создаю карточку 'Почтовые ящики ЖК Давинчи комфорт'...")
url = "https://api.trello.com/1/cards"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'idList': list_ids["Очередь"],
    'name': '🚨 Почтовые ящики ЖК Давинчи комфорт',
    'desc': 'СРОЧНО'
}
r = requests.post(url, params=params)
if r.status_code != 200:
    print(f"❌ Ошибка создания карточки: {r.text}")
    exit(1)

card = r.json()
card_id = card['id']
print(f"✅ Карточка создана: {card['shortUrl']}")

# 4. Добавляем чеклист с подзадачами
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

# 5. Обновляем конфиг
print("\n💾 Обновляю конфиг...")
config['boards']['ced_supervision'] = {
    'id': board_id,
    'name': 'СЭД Акторский надзор',
    'url': board_url,
    'lists': {
        'backlog': {'id': list_ids['Очередь'], 'name': 'Очередь'},
        'inProgress': {'id': list_ids['В работе'], 'name': 'В работе'},
        'onPayment': {'id': list_ids['На оплате'], 'name': 'На оплате'},
        'onInstallation': {'id': list_ids['На монтаже'], 'name': 'На монтаже'},
        'done': {'id': list_ids['Готово'], 'name': 'Готово'},
        'notRelevant': {'id': list_ids['Не актуально'], 'name': 'Не актуально'}
    }
}

with open('/home/axis/openclaw/trello-config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("✅ Конфиг обновлён")
print(f"\n🎉 Готово! Доска: {board_url}")
