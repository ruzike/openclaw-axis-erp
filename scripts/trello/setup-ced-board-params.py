#!/usr/bin/env python3
"""Настройка параметров доски СЭД Акторский надзор"""
import json
import requests

# Загружаем конфиг
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
board_id = config['boards']['ced_supervision']['id']

print("🏷️  Создаю метки приоритетов...")

# Создаём метки приоритетов
labels = [
    {"name": "Critical", "color": "red"},
    {"name": "High", "color": "orange"},
    {"name": "Medium", "color": "yellow"},
    {"name": "Low", "color": "green"}
]

label_ids = {}
for label in labels:
    url = "https://api.trello.com/1/labels"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'name': label['name'],
        'color': label['color'],
        'idBoard': board_id
    }
    r = requests.post(url, params=params)
    if r.status_code == 200:
        label_data = r.json()
        label_ids[label['name']] = label_data['id']
        print(f"  ✅ {label['color']} {label['name']}")
    else:
        print(f"  ❌ {label['name']}: {r.text}")

print("\n👤 Получаю ID Руслана в Trello...")
# Получаем информацию о пользователе (владельце токена)
url = "https://api.trello.com/1/members/me"
params = {
    'key': API_KEY,
    'token': TOKEN
}
r = requests.get(url, params=params)
if r.status_code != 200:
    print(f"❌ Ошибка получения профиля: {r.text}")
    exit(1)

user = r.json()
user_id = user['id']
username = user['username']
print(f"✅ {username} (ID: {user_id})")

print("\n📌 Назначаю Руслана на карточки...")

# Получаем все карточки из колонки "Очередь"
list_id = config['boards']['ced_supervision']['lists']['backlog']['id']
url = f"https://api.trello.com/1/lists/{list_id}/cards"
params = {
    'key': API_KEY,
    'token': TOKEN
}
r = requests.get(url, params=params)
if r.status_code != 200:
    print(f"❌ Ошибка получения карточек: {r.text}")
    exit(1)

cards = r.json()

# Добавляем Руслана на каждую карточку
for card in cards:
    url = f"https://api.trello.com/1/cards/{card['id']}/idMembers"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'value': user_id
    }
    r = requests.post(url, params=params)
    if r.status_code == 200:
        print(f"  ✅ {card['name']}")
    else:
        print(f"  ❌ {card['name']}: {r.text}")

print("\n🎉 Готово! Доска настроена.")
print(f"📋 https://trello.com/b/xYgWoBeX")
