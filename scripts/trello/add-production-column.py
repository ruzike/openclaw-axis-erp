#!/usr/bin/env python3
"""Добавление колонки 'В производстве' на доску СЭД"""
import json
import requests

# Загружаем конфиг
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
board_id = config['boards']['ced_supervision']['id']

print("📝 Создаю колонку 'В производстве'...")

# Создаём новую колонку
url = "https://api.trello.com/1/lists"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'name': 'В производстве',
    'idBoard': board_id,
    'pos': 3  # Позиция после "На оплате" (Очередь=1, В работе=2, На оплате=3, В производстве=4)
}
r = requests.post(url, params=params)
if r.status_code != 200:
    print(f"❌ Ошибка создания колонки: {r.text}")
    exit(1)

list_data = r.json()
list_id = list_data['id']
print(f"✅ Колонка создана (ID: {list_id})")

# Обновляем конфиг
print("\n💾 Обновляю конфиг...")
config['boards']['ced_supervision']['lists']['inProduction'] = {
    'id': list_id,
    'name': 'В производстве'
}

with open('/home/axis/openclaw/trello-config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("✅ Конфиг обновлён")
print(f"\n🎉 Готово! Новый порядок колонок:")
print("1. Очередь")
print("2. В работе")
print("3. На оплате")
print("4. В производстве ← NEW")
print("5. На монтаже")
print("6. Готово")
print("7. Не актуально")
