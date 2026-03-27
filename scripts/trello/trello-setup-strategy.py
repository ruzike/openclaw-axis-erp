#!/usr/bin/env python3
"""Настройка двухдосочной структуры Trello"""
import json
import requests

# Загружаем текущий конфиг
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

# 1. Переименовываем текущую доску Mission Control → Производство
print("📋 Переименовываем 'Mission Control' → 'Производство'...")
board_id = config['board']['id']
url = f"https://api.trello.com/1/boards/{board_id}"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'name': 'Производство'
}
r = requests.put(url, params=params)
if r.status_code == 200:
    print("✅ Доска переименована")
else:
    print(f"❌ Ошибка переименования: {r.text}")

# 2. Создаём новую доску "Стратегия"
print("\n🎯 Создаём доску 'Стратегия'...")
url = "https://api.trello.com/1/boards/"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'name': 'Стратегия',
    'defaultLists': 'false'  # Не создавать дефолтные колонки
}
r = requests.post(url, params=params)
if r.status_code == 200:
    strategy_board = r.json()
    strategy_board_id = strategy_board['id']
    print(f"✅ Доска создана: {strategy_board['url']}")
else:
    print(f"❌ Ошибка создания доски: {r.text}")
    exit(1)

# 3. Создаём колонки в доске "Стратегия"
columns = [
    "💡 Идеи",
    "🎯 Цели квартала",
    "📅 Этот месяц",
    "🔄 Внедряю",
    "✅ Внедрено",
    "📊 Метрики"
]

strategy_lists = {}
for idx, col_name in enumerate(columns):
    print(f"  Создаём колонку: {col_name}...")
    url = "https://api.trello.com/1/lists"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'name': col_name,
        'idBoard': strategy_board_id,
        'pos': idx + 1
    }
    r = requests.post(url, params=params)
    if r.status_code == 200:
        list_data = r.json()
        # Ключ без эмодзи для удобства
        key = col_name.split(' ', 1)[1].lower().replace(' ', '_')
        strategy_lists[key] = {
            'id': list_data['id'],
            'name': col_name
        }
        print(f"    ✅ {col_name}")
    else:
        print(f"    ❌ Ошибка: {r.text}")

# 4. Переименовываем колонки в "Производство" (русификация)
print("\n🏭 Обновляем колонки 'Производство'...")
production_renames = {
    'backlog': 'Очередь',
    'inProgress': 'В работе',
    'done': 'Готово'
}

production_lists = {}
for key, old_data in config['lists'].items():
    if key in production_renames:
        new_name = production_renames[key]
        url = f"https://api.trello.com/1/lists/{old_data['id']}"
        params = {
            'key': API_KEY,
            'token': TOKEN,
            'name': new_name
        }
        r = requests.put(url, params=params)
        if r.status_code == 200:
            production_lists[key] = {
                'id': old_data['id'],
                'name': new_name
            }
            print(f"  ✅ {new_name}")
        else:
            print(f"  ❌ Ошибка: {r.text}")
    else:
        # Оставляем как есть
        production_lists[key] = old_data

# 5. Сохраняем обновлённый конфиг
new_config = {
    'boards': {
        'production': {
            'id': board_id,
            'name': 'Производство',
            'url': config['board']['url'],
            'lists': production_lists
        },
        'strategy': {
            'id': strategy_board_id,
            'name': 'Стратегия',
            'url': strategy_board['url'],
            'lists': strategy_lists
        }
    },
    'api': config['api']
}

with open('/home/axis/openclaw/trello-config.json', 'w') as f:
    json.dump(new_config, f, indent=2, ensure_ascii=False)

print("\n✅ Конфигурация обновлена!")
print("\n📊 Структура:")
print(f"  🏭 Производство: {config['board']['url']}")
print(f"  🎯 Стратегия: {strategy_board['url']}")
