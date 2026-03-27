#!/usr/bin/env python3
"""Назначить Руслана на последнюю созданную карточку"""
import json
import requests

# Загружаем конфиг
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

# ID карточки из вывода
card_id = "2W6WXgKW"

print("👤 Получаю ID Руслана...")
url = "https://api.trello.com/1/members/me"
params = {
    'key': API_KEY,
    'token': TOKEN
}
r = requests.get(url, params=params)
if r.status_code != 200:
    print(f"❌ Ошибка: {r.text}")
    exit(1)

user = r.json()
user_id = user['id']

print(f"✅ {user['username']}")

print("\n📌 Назначаю Руслана на карточку...")
url = f"https://api.trello.com/1/cards/{card_id}/idMembers"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'value': user_id
}
r = requests.post(url, params=params)
if r.status_code == 200:
    print(f"✅ Руслан назначен")
else:
    print(f"❌ Ошибка: {r.text}")
