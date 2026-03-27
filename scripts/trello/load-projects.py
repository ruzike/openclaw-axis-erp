#!/usr/bin/env python3
"""Загрузка проектов в Trello Production"""
import requests
import json
import time

with open('/home/axis/openclaw/trello-config.json') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
BOARD_ID = config['boards']['production']['id']
LISTS = config['boards']['production']['lists']

# ID меток
LABELS = {
    'critical': '6981d92a2e52fda8adfae0f0',
    'medium': '6981d92b21b31c8e581da52d',
    'low': '6981d92b20ee8206f3ab6f17'
}

PROJECTS = [
    {
        'name': '🏘️ ЖК ТОКИО',
        'stages': [
            ('Дизайн/Концепт', '🔴', 'Нужно делать'),
            ('Визуализация', '🔴', 'Нужно делать'),
            ('Рабочка', '🔴', 'Нужно делать'),
            ('Благоустройство', '🟡', 'Доработать'),
        ]
    },
    {
        'name': '✈️ АЭРОПОРТ',
        'stages': [
            ('Дизайн/Концепт', '🟢', 'Готово'),
            ('Визуализация', '🟢', 'Готово'),
            ('Рабочка', '🔴', 'В процессе'),
            ('Благоустройство', '🔴', 'Дизайн + РД'),
        ]
    },
    {
        'name': '🏘️ ЖК ЛОНДОН',
        'stages': [
            ('Дизайн/Концепт', '🔴', 'Нужно делать'),
            ('Визуализация', '🔴', 'Нужно делать'),
            ('Рабочка', '🔴', 'Нужно делать'),
            ('Благоустройство', '🟡', 'Доработать'),
        ]
    },
    {
        'name': '🏢 ЕСИЛЬ СИТИ 2',
        'stages': [
            ('Дизайн/Концепт', '🟢', 'Готово'),
            ('Визуализация', '🔴', 'Сделать виз'),
            ('Рабочка', '🟢', 'Готово'),
            ('Благоустройство', '🔴', 'РД'),
        ]
    },
    {
        'name': '🏢 СЭД ОФИС',
        'stages': [
            ('Дизайн/Концепт', '🔴', 'Дизайн (Интерьер+Фасад)'),
            ('Визуализация', '🔴', 'Нужно делать'),
            ('Рабочка', '🔴', 'Нужно делать'),
            ('Благоустройство', '🟡', 'Немного'),
        ]
    },
    {
        'name': '🏢 СЭД Костанай',
        'stages': [
            ('Дизайн/Концепт', '🟡', 'Холлы'),
            ('Визуализация', '🟡', 'Холлы'),
            ('Рабочка', '🔴', 'Нужно делать'),
            ('Благоустройство', '🔴', 'Дизайн + РД'),
        ]
    },
    {
        'name': '🏢 СЭД П-павловск',
        'stages': [
            ('Дизайн/Концепт', '🟡', 'Холлы'),
            ('Визуализация', '🟡', 'Холлы'),
            ('Рабочка', '🔴', 'Нужно делать'),
            ('Благоустройство', '🔴', 'Дизайн + РД'),
        ]
    },
    {
        'name': '🏢 Австрийский 4',
        'stages': [
            ('Дизайн/Концепт', '🟢', 'Готово'),
            ('Визуализация', '🟢', 'Готово'),
            ('Рабочка', '🟢', 'Готово'),
            ('Благоустройство', '🟡', 'Доработать'),
        ]
    },
]

def create_card_with_checklist(project):
    """Создать карточку с чеклистом"""
    name = project['name']
    stages = project['stages']
    
    # Определить колонку и метки
    has_critical = any(s[1] == '🔴' for s in stages)
    has_medium = any(s[1] == '🟡' for s in stages)
    all_done = all(s[1] == '🟢' for s in stages)
    
    # Выбрать колонку
    if all_done:
        list_id = LISTS['done']['id']
    elif has_critical:
        list_id = LISTS['inProgress']['id']
    else:
        list_id = LISTS['backlog']['id']
    
    # Сформировать описание
    description = "**Этапы проекта:**\n\n"
    for stage_name, status, note in stages:
        description += f"{status} **{stage_name}**: {note}\n"
    
    # Создать карточку
    url = 'https://api.trello.com/1/cards'
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'idList': list_id,
        'name': name,
        'desc': description,
        'pos': 'top'
    }
    
    r = requests.post(url, params=params)
    if r.status_code != 200:
        print(f"❌ Ошибка создания {name}: {r.text}")
        return None
    
    card = r.json()
    card_id = card['id']
    
    # Добавить метки
    labels_to_add = []
    if has_critical:
        labels_to_add.append(LABELS['critical'])
    if has_medium:
        labels_to_add.append(LABELS['medium'])
    
    for label_id in labels_to_add:
        url = f'https://api.trello.com/1/cards/{card_id}/idLabels'
        params = {
            'key': API_KEY,
            'token': TOKEN,
            'value': label_id
        }
        requests.post(url, params=params)
    
    # Создать чеклист
    url = f'https://api.trello.com/1/cards/{card_id}/checklists'
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'name': 'Этапы'
    }
    r = requests.post(url, params=params)
    if r.status_code != 200:
        print(f"⚠️ Не удалось создать чеклист для {name}")
    else:
        checklist = r.json()
        checklist_id = checklist['id']
        
        # Добавить элементы чеклиста
        for stage_name, status, note in stages:
            item_name = f"{status} {stage_name}: {note}"
            checked = 'true' if status == '🟢' else 'false'
            
            url = f'https://api.trello.com/1/checklists/{checklist_id}/checkItems'
            params = {
                'key': API_KEY,
                'token': TOKEN,
                'name': item_name,
                'checked': checked
            }
            requests.post(url, params=params)
    
    time.sleep(0.5)  # Rate limiting
    
    return card

# Создать все проекты
created = []
for project in PROJECTS:
    print(f"📝 Создаю: {project['name']}...")
    card = create_card_with_checklist(project)
    if card:
        created.append({
            'name': project['name'],
            'url': card['shortUrl']
        })
        print(f"   ✅ {card['shortUrl']}")

print(f"\n{'='*60}")
print(f"✅ Создано проектов: {len(created)}")
print('='*60)

for item in created:
    print(f"• {item['name']}")
    print(f"  🔗 {item['url']}")
