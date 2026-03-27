#!/usr/bin/env python3
"""Get checklist ID and add item to existing checklist"""
import json
import requests
import sys

# Load config
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

card_id = sys.argv[1] if len(sys.argv) > 1 else '6998801b4614fa9077b4187c'
checklist_name = sys.argv[2] if len(sys.argv) > 2 else 'Задачи'
new_item = sys.argv[3] if len(sys.argv) > 3 else 'Подготовить дизайнерский альбом по благоустройству'

# Get all checklists for the card
url = f"https://api.trello.com/1/cards/{card_id}/checklists"
params = {'key': API_KEY, 'token': TOKEN}
r = requests.get(url, params=params)

if r.status_code == 200:
    checklists = r.json()
    print(f"📋 Чеклисты на карточке:")
    for checklist in checklists:
        print(f"  • {checklist['name']} (ID: {checklist['id']})")

    # Find the checklist by name
    target_checklist = None
    for checklist in checklists:
        if checklist['name'] == checklist_name:
            target_checklist = checklist
            break

    if target_checklist:
        print(f"\n✅ Найден чеклист: {target_checklist['name']} (ID: {target_checklist['id']})")

        # Add the new item
        url = f"https://api.trello.com/1/checklists/{target_checklist['id']}/checkItems"
        params = {
            'key': API_KEY,
            'token': TOKEN,
            'name': new_item,
            'pos': 'bottom'
        }
        r = requests.post(url, params=params)

        if r.status_code == 200:
            item = r.json()
            print(f"✅ Добавлен пункт: {new_item}")
            print(f"   Item ID: {item['id']}")
        else:
            print(f"❌ Ошибка добавления пункта: {r.text}")
    else:
        print(f"❌ Чеклист '{checklist_name}' не найден")
else:
    print(f"❌ Ошибка: {r.text}")
