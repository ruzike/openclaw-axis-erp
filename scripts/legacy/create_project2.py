#!/usr/bin/env python3
"""Create airport arkalys card and checklist"""
import json
import requests

# Load config
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

# Get C3 board
board_key = 'c3'
board = config['boards'][board_key]
board_id = board['id']

# Get all lists on the board
board_url = f"https://api.trello.com/1/boards/{board_id}"
params = {'key': API_KEY, 'token': TOKEN, 'fields': 'name'}
r = requests.get(board_url, params=params)
if r.status_code != 200:
    print(f"❌ Error getting board info: {r.text}")
    exit(1)

board_data = r.json()
lists_data = board_data.get('lists', [])

print("Available lists on C3 board:")
for lst in lists_data:
    print(f"  • {lst['name']} (ID: {lst['id']})")

# Create card in the first list (backlog)
card_url = f"https://api.trello.com/1/cards"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'idBoard': board_id,
    'idList': lists_data[0]['id'],  # Use first list
    'name': 'АЭРОПОРТ АРКАЛЫК: Рабочий проект фасада',
    'desc': 'Главная карточка проекта. Включает чеклист с 6 ключевыми задачами.'
}

print(f"\nCreating main card in list '{lists_data[0]['name']}'...")
r = requests.post(card_url, params=params)
if r.status_code == 200:
    card = r.json()
    card_id = card['id']
    print(f"✅ Main card created: {card['name']}")
    print(f"🔗 {card['shortUrl']}")
else:
    print(f"❌ Error: {r.text}")
    print(f"Response: {r.json()}")
    exit(1)

# Define checklist items
checklist_name = "Ключевые задачи проекта"
items = [
    "Провести обследование текущего состояния фасада",
    "Разработать дизайн-проект фасада с учетом требований заказчика",
    "Подобрать материалы для отделки фасада",
    "Разработать рабочую документацию (КР и РД)",
    "Организовать тендер на выполнение работ",
    "Контролировать и oversee выполнение работ по этапам"
]

# Create checklist
checklist_url = f"https://api.trello.com/1/checklists"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'idCard': card_id,
    'name': checklist_name
}

print(f"\nCreating checklist '{checklist_name}'...")
r = requests.post(checklist_url, params=params)
if r.status_code == 200:
    checklist = r.json()
    checklist_id = checklist['id']
    print(f"✅ Checklist created: {checklist['name']}")
else:
    print(f"❌ Error creating checklist: {r.text}")
    exit(1)

# Add checklist items
print(f"\nAdding {len(items)} items to checklist...")
success_count = 0
for i, item in enumerate(items, 1):
    item_url = f"https://api.trello.com/1/checklists/{checklist_id}/checkItems"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'name': item,
        'pos': str(i)
    }
    r = requests.post(item_url, params=params)
    if r.status_code == 200:
        print(f"  {i}. {item}")
        success_count += 1
    else:
        print(f"  ❌ Failed to add '{item}': {r.text}")

print(f"\n✅ Total items added: {success_count}/{len(items)}")

# Update card description
desc_url = f"https://api.trello.com/1/cards/{card_id}"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'desc': f'''**АЭРОПОРТ АРКАЛЫК: Рабочий проект фасада**

🏠 **Проект:** Аэропорт Аркалык - Фасад
📋 **Главная задача:** Выполнить рабочий проект фасада с соблюдением всех требований заказчика

## 📋 Чеклист задач:
{checklist_name}

---
*Создано: 2026-02-20*
*Статус: В процессе*'''
}

r = requests.put(desc_url, params=params)
if r.status_code == 200:
    print(f"\n✅ Card description updated")
else:
    print(f"❌ Error updating description: {r.text}")

print(f"\n{'='*60}")
print(f"✅ Проект успешно создан!")
print(f"{'='*60}")
print(f"Карточка: {card['name']}")
print(f"ID: {card_id}")
print(f"URL: {card['shortUrl']}")
print(f"Чеклист: {checklist_name}")
print(f"{'='*60}")
