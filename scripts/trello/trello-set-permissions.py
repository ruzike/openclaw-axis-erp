#!/usr/bin/env python3
"""Настройка прав доступа к доскам"""
import json
import requests

with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

# Доска "Стратегия" — только Руслан (приватная)
strategy_id = config['boards']['strategy']['id']
print("🔒 Настраиваю доступ к 'Стратегия' (приватная)...")
url = f"https://api.trello.com/1/boards/{strategy_id}"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'prefs/permissionLevel': 'private'
}
r = requests.put(url, params=params)
if r.status_code == 200:
    print("✅ Доска 'Стратегия' теперь приватная")
else:
    print(f"❌ Ошибка: {r.text}")

# Доска "Производство" — доступна команде
production_id = config['boards']['production']['id']
print("\n👥 Настраиваю доступ к 'Производство' (командная)...")
url = f"https://api.trello.com/1/boards/{production_id}"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'prefs/permissionLevel': 'org'  # Доступна всем в организации
}
r = requests.put(url, params=params)
if r.status_code == 200:
    print("✅ Доска 'Производство' доступна команде")
else:
    print(f"❌ Ошибка: {r.text}")

print("\n✅ Права доступа настроены!")
