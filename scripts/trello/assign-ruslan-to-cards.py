#!/usr/bin/env python3
"""Назначить Руслана на все карточки доски СЭД"""
import json
import requests

# Загружаем конфиг
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
board_id = config['boards']['ced_supervision']['id']

print("👤 Получаю ID Руслана в Trello...")
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

print("\n📋 Получаю все карточки доски...")
url = f"https://api.trello.com/1/boards/{board_id}/cards"
params = {
    'key': API_KEY,
    'token': TOKEN
}
r = requests.get(url, params=params)
if r.status_code != 200:
    print(f"❌ Ошибка получения карточек: {r.text}")
    exit(1)

cards = r.json()
print(f"Найдено карточек: {len(cards)}")

print("\n📌 Назначаю Руслана на карточки...")
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

print("\n🎉 Готово!")
