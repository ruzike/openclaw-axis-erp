#!/usr/bin/env python3
"""Trello CLI для управления задачами (двухдосочная структура)"""
import json
import requests
import sys
import time

# Загружаем конфиг
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

# ──────────────────────────────────────────────────────────────
# Rate-limit-aware request wrapper
# Trello allows ~180 req/min per token. On 429 we back off and retry.
# ──────────────────────────────────────────────────────────────
def trello_request(method, url, params=None, max_retries=4, **kwargs):
    """Wrapper вокруг requests с авто-ретраем при rate limit (429)."""
    if params is None:
        params = {}
    params.setdefault('key', API_KEY)
    params.setdefault('token', TOKEN)

    for attempt in range(max_retries):
        r = getattr(requests, method)(url, params=params, **kwargs)
        if r.status_code == 429:
            retry_after = int(r.headers.get('Retry-After', 10))
            wait = retry_after + attempt * 5
            print(f"⏳ Rate limit hit — ждём {wait}с (попытка {attempt+1}/{max_retries})…", file=sys.stderr)
            time.sleep(wait)
            continue
        return r
    # Last attempt
    return r

def get_board_and_list(board_name, list_name):
    """Получить ID доски и колонки"""
    if board_name not in config['boards']:
        print(f"❌ Доска '{board_name}' не найдена. Доступные: {', '.join(config['boards'].keys())}")
        return None, None
    
    board = config['boards'][board_name]
    if list_name not in board['lists']:
        print(f"❌ Колонка '{list_name}' не найдена на доске '{board_name}'")
        print(f"Доступные: {', '.join(board['lists'].keys())}")
        return None, None
    
    return board['id'], board['lists'][list_name]['id']

def create_card(board_name, name, list_name, desc=''):
    """Создать карточку на указанной доске"""
    board_id, list_id = get_board_and_list(board_name, list_name)
    if not list_id:
        return None
    
    url = f"https://api.trello.com/1/cards"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'idList': list_id,
        'name': name,
        'desc': desc
    }
    r = requests.post(url, params=params)
    if r.status_code == 200:
        card = r.json()
        board_display = config['boards'][board_name]['name']
        print(f"✅ Карточка создана на '{board_display}': {card['name']}")
        print(f"🔗 {card['shortUrl']}")
        return card
    else:
        print(f"❌ Ошибка: {r.text}")
        return None

def update_card(card_id, name=None, desc=None):
    """Обновить название и/или описание карточки"""
    url = f"https://api.trello.com/1/cards/{card_id}"
    params = {
        'key': API_KEY,
        'token': TOKEN
    }
    if name:
        params['name'] = name
    if desc:
        params['desc'] = desc
    
    r = requests.put(url, params=params)
    if r.status_code == 200:
        card = r.json()
        print(f"✅ Карточка обновлена: {card['name']}")
        print(f"🔗 {card['shortUrl']}")
        return True
    else:
        print(f"❌ Ошибка: {r.text}")
        return False

def delete_card(card_id):
    """Удалить карточку"""
    url = f"https://api.trello.com/1/cards/{card_id}"
    params = {
        'key': API_KEY,
        'token': TOKEN
    }
    r = requests.delete(url, params=params)
    if r.status_code == 200:
        print(f"✅ Карточка удалена: {card_id}")
        return True
    else:
        print(f"❌ Ошибка: {r.text}")
        return False

def move_card(card_id, board_name, list_name):
    """Переместить карточку в другую колонку"""
    board_id, list_id = get_board_and_list(board_name, list_name)
    if not list_id:
        return False
    
    url = f"https://api.trello.com/1/cards/{card_id}"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'idList': list_id
    }
    r = requests.put(url, params=params)
    if r.status_code == 200:
        list_display = config['boards'][board_name]['lists'][list_name]['name']
        print(f"✅ Карточка перемещена в {list_display}")
        return True
    else:
        print(f"❌ Ошибка: {r.text}")
        return False

def list_cards(board_name, list_name):
    """Показать все карточки в колонке"""
    board_id, list_id = get_board_and_list(board_name, list_name)
    if not list_id:
        return []
    
    url = f"https://api.trello.com/1/lists/{list_id}/cards"
    params = {'key': API_KEY, 'token': TOKEN}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        cards = r.json()
        list_display = config['boards'][board_name]['lists'][list_name]['name']
        if not cards:
            print(f"📋 {list_display}: пусто")
        else:
            print(f"📋 {list_display}:")
            for card in cards:
                print(f"  • {card['name']} ({card['id']})")
        return cards
    else:
        print(f"❌ Ошибка: {r.text}")
        return []

def read_card(card_id):
    """Прочитать описание карточки по ID"""
    url = f"https://api.trello.com/1/cards/{card_id}"
    params = {'key': API_KEY, 'token': TOKEN, 'fields': 'name,desc,url,idList,labels'}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        card = r.json()
        print(f"📋 Карточка: {card['name']}")
        print(f"🔗 {card.get('url', 'N/A')}")
        if card.get('labels'):
            print(f"🏷️ Метки: {', '.join(l['name'] for l in card['labels'] if l.get('name'))}")
        print(f"\n📝 Описание:\n{card.get('desc', '(пусто)')}")
        return card
    else:
        print(f"❌ Ошибка: {r.text}")
        return None

def create_list(board_name, name, pos=None):
    """Создать новую колонку на доске"""
    if board_name not in config['boards']:
        print(f"❌ Доска '{board_name}' не найдена. Доступные: {', '.join(config['boards'].keys())}")
        return None
    
    board_id = config['boards'][board_name]['id']
    url = "https://api.trello.com/1/lists"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'name': name,
        'idBoard': board_id
    }
    if pos is not None:
        params['pos'] = pos
    
    r = requests.post(url, params=params)
    if r.status_code == 200:
        lst = r.json()
        print(f"✅ Колонка создана: {lst['name']} (ID: {lst['id']})")
        return lst
    else:
        print(f"❌ Ошибка: {r.text}")
        return None

def get_member_id(member_name):
    """Получить Trello ID члена по имени или username"""
    if member_name in config['members']:
        return config['members'][member_name]['trello_id']
    
    # Проверяем по username
    for member_id, member_info in config['members'].items():
        if member_info.get('username', '').lower() == member_name.lower():
            return member_info['trello_id']
    
    return None

def get_card_members(card_id):
    """Показать всех участников карточки"""
    url = f"https://api.trello.com/1/cards/{card_id}/members"
    params = {'key': API_KEY, 'token': TOKEN}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        members = r.json()
        if not members:
            print("👥 Участники: нет")
        else:
            print("👥 Участники карточки:")
            for member in members:
                username = member.get('username', 'N/A')
                full_name = member.get('fullName', 'N/A')
                print(f"   • {full_name} (@{username})")
        return members
    else:
        print(f"❌ Ошибка: {r.text}")
        return []

def assign_members_to_card(card_id, member_names):
    """Добавить участников в карточку"""
    card = read_card(card_id)
    if not card:
        return False
    
    success_count = 0
    for member_name in member_names:
        member_id = get_member_id(member_name)
        if not member_id:
            print(f"❌ Участник '{member_name}' не найден")
            continue
        
        url = f"https://api.trello.com/1/cards/{card_id}/idMembers"
        params = {
            'key': API_KEY,
            'token': TOKEN,
            'value': member_id
        }
        r = requests.post(url, params=params)
        if r.status_code == 200:
            print(f"✅ {member_name} добавлен в карточку")
            success_count += 1
        else:
            print(f"❌ Ошибка добавления {member_name}: {r.text}")
    
    print(f"\n📊 Добавлено участников: {success_count}/{len(member_names)}")
    return success_count > 0

def unassign_members_from_card(card_id, member_names):
    """Удалить участников из карточки"""
    card = read_card(card_id)
    if not card:
        return False
    
    success_count = 0
    for member_name in member_names:
        member_id = get_member_id(member_name)
        if not member_id:
            print(f"❌ Участник '{member_name}' не найден")
            continue
        
        url = f"https://api.trello.com/1/cards/{card_id}/idMembers/{member_id}"
        params = {
            'key': API_KEY,
            'token': TOKEN
        }
        r = requests.delete(url, params=params)
        if r.status_code == 200:
            print(f"✅ {member_name} удалён из карточки")
            success_count += 1
        else:
            print(f"❌ Ошибка удаления {member_name}: {r.text}")
    
    print(f"\n📊 Удалено участников: {success_count}/{len(member_names)}")
    return success_count > 0

def create_checklist(card_id, checklist_name, items):
    """Создать чеклист в карточке с элементами"""
    # Сначала создаем чеклист
    url = f"https://api.trello.com/1/checklists"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'idCard': card_id,
        'name': checklist_name
    }
    r = requests.post(url, params=params)
    if r.status_code != 200:
        print(f"❌ Ошибка создания чеклиста: {r.text}")
        return None
    
    checklist = r.json()
    checklist_id = checklist['id']
    
    # Добавляем элементы в чеклист
    success_count = 0
    for item in items:
        url = f"https://api.trello.com/1/checklists/{checklist_id}/checkItems"
        params = {
            'key': API_KEY,
            'token': TOKEN,
            'name': item,
            'pos': 'bottom'
        }
        r = requests.post(url, params=params)
        if r.status_code == 200:
            print(f"✅ Добавлен пункт: {item}")
            success_count += 1
        else:
            print(f"❌ Ошибка добавления пункта '{item}': {r.text}")
    
    print(f"\n📊 Чеклист '{checklist_name}' создан. Пунктов добавлено: {success_count}/{len(items)}")
    return checklist_id

def show_checklists(card_id):
    """Показать все чеклисты в карточке"""
    url = f"https://api.trello.com/1/cards/{card_id}/checklists"
    params = {'key': API_KEY, 'token': TOKEN}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(f"❌ Ошибка получения чеклистов: {r.text}")
        return []
    
    checklists = r.json()
    if not checklists:
        print("📋 Чеклисты: нет")
        return checklists
    
    for checklist in checklists:
        print(f"\n📋 Чеклист: {checklist['name']}")
        for item in checklist.get('checkItems', []):
            status = "✅" if item['state'] == 'complete' else "⬜"
            print(f"   {status} {item['name']}")
    
    return checklists

def toggle_checklist_item(card_id, item_id, state):
    """Переключить состояние пункта чеклиста"""
    url = f"https://api.trello.com/1/cards/{card_id}/checkItem/{item_id}"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'state': state
    }
    r = requests.put(url, params=params)
    if r.status_code == 200:
        print(f"✅ Пункт {state}: {item_id}")
        return True
    else:
        print(f"❌ Ошибка переключения: {r.text}")
        return False

def delete_checklist_item(card_id, item_id):
    """Удалить пункт чеклиста"""
    url = f"https://api.trello.com/1/cards/{card_id}/checkItem/{item_id}"
    params = {
        'key': API_KEY,
        'token': TOKEN
    }
    r = requests.delete(url, params=params)
    if r.status_code == 200:
        print(f"✅ Пункт удален: {item_id}")
        return True
    else:
        print(f"❌ Ошибка удаления: {r.text}")
        return False

def show_checklist_items(card_id, checklist_id):
    """Показать пункты конкретного чеклиста"""
    url = f"https://api.trello.com/1/checklists/{checklist_id}"
    params = {'key': API_KEY, 'token': TOKEN}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(f"❌ Ошибка получения чеклиста: {r.text}")
        return []
    
    checklist = r.json()
    print(f"\n📋 {checklist['name']}")
    for item in checklist.get('checkItems', []):
        status = "✅" if item['state'] == 'complete' else "⬜"
        print(f"   {status} {item['name']} (ID: {item['id']})")
    return checklist

def show_all_boards():
    """Показать все доски и их колонки"""
    print("📊 Доступные доски:\n")
    for key, board in config['boards'].items():
        print(f"🎯 {board['name']} ({key})")
        print(f"   URL: {board['url']}")
        print(f"   Колонки:")
        for list_key, list_data in board['lists'].items():
            print(f"     • {list_data['name']} ({list_key})")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование:")
        print("  trello.py read <card_id> - прочитать описание карточки")
        print("  trello.py boards - показать все доски")
        print("  trello.py create <board> 'Название' <list> ['Описание']")
        print("  trello.py update <card_id> ['Новое название'] ['Новое описание']")
        print("  trello.py delete <card_id>")
        print("  trello.py move <card_id> <board> <list>")
        print("  trello.py list <board> <list>")
        print("  trello.py members <card_id> - показать участников карточки")
        print("  trello.py assign <card_id> <member1> [<member2> ...] - добавить участников")
        print("  trello.py unassign <card_id> <member1> [<member2> ...] - удалить участников")
        print("  trello.py checklist <card_id> - показать чеклисты карточки")
        print("  trello.py show_checklist <card_id> <checklist_id> - показать пункты конкретного чеклиста")
        print("  trello.py add-checklist <card_id> 'Название' 'Пункт1' ['Пункт2' ...] - создать чеклист")
        print("  trello.py delete-checkitem <card_id> <item_id> - удалить пункт")
        print("  trello.py toggle-checkitem <card_id> <item_id> <state> - отметить пункт (complete/incomplete)")
        print("\nДоски: production, strategy, ced_supervision, c3")
        print("Колонки Production: unsorted, backlog, today, inProgress, done, notRelevant")
        print("Колонки Strategy: идеи, цели_квартала, этот_месяц, внедряю, внедрено, метрики")
        print("Колонки CED: backlog, inProgress, onEstimate, onPayment, onInstallation, done, notRelevant, inProduction")
        print("Колонки C3: backlog, preparation, inProgress, review, corrections, done")
        print("\nУчастники: ruslan, miras, bakhytzhan")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'boards':
        show_all_boards()
    
    elif command == 'read':
        if len(sys.argv) < 3:
            print("❌ Использование: trello.py read <card_id>")
            sys.exit(1)
        card_id = sys.argv[2]
        read_card(card_id)
    
    elif command == 'create':
        if len(sys.argv) < 5:
            print("❌ Использование: trello.py create <board> 'Название' <list> ['Описание']")
            sys.exit(1)
        board_name = sys.argv[2]
        name = sys.argv[3]
        list_name = sys.argv[4]
        desc = sys.argv[5] if len(sys.argv) > 5 else ''
        create_card(board_name, name, list_name, desc)
    
    elif command == 'update':
        if len(sys.argv) < 3:
            print("❌ Использование: trello.py update <card_id> ['Новое название'] ['Новое описание']")
            sys.exit(1)
        card_id = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else None
        desc = sys.argv[4] if len(sys.argv) > 4 else None
        update_card(card_id, name, desc)
    
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("❌ Использование: trello.py delete <card_id>")
            sys.exit(1)
        card_id = sys.argv[2]
        delete_card(card_id)
    
    elif command == 'move':
        if len(sys.argv) < 5:
            print("❌ Использование: trello.py move <card_id> <board> <list>")
            sys.exit(1)
        card_id = sys.argv[2]
        board_name = sys.argv[3]
        list_name = sys.argv[4]
        move_card(card_id, board_name, list_name)
    
    elif command == 'list':
        if len(sys.argv) < 4:
            print("❌ Использование: trello.py list <board> <list>")
            sys.exit(1)
        board_name = sys.argv[2]
        list_name = sys.argv[3]
        list_cards(board_name, list_name)
    
    elif command == 'create_list':
        if len(sys.argv) < 4:
            print("❌ Использование: trello.py create_list <board> 'Название' [позиция]")
            sys.exit(1)
        board_name = sys.argv[2]
        name = sys.argv[3]
        pos = sys.argv[4] if len(sys.argv) > 4 else None
        create_list(board_name, name, pos)
    
    elif command == 'members':
        if len(sys.argv) < 3:
            print("❌ Использование: trello.py members <card_id>")
            sys.exit(1)
        card_id = sys.argv[2]
        get_card_members(card_id)
    
    elif command == 'assign':
        if len(sys.argv) < 4:
            print("❌ Использование: trello.py assign <card_id> <member1> [<member2> ...]")
            print("Доступные участники: ruslan, miras, bakhytzhan")
            sys.exit(1)
        card_id = sys.argv[2]
        member_names = sys.argv[3:]
        assign_members_to_card(card_id, member_names)
    
    elif command == 'unassign':
        if len(sys.argv) < 4:
            print("❌ Использование: trello.py unassign <card_id> <member1> [<member2> ...]")
            print("Доступные участники: ruslan, miras, bakhytzhan")
            sys.exit(1)
        card_id = sys.argv[2]
        member_names = sys.argv[3:]
        unassign_members_from_card(card_id, member_names)

    elif command == 'checklist':
        if len(sys.argv) < 3:
            print("❌ Использование: trello.py checklist <card_id>")
            sys.exit(1)
        card_id = sys.argv[2]
        show_checklists(card_id)

    elif command == 'show_checklist':
        if len(sys.argv) < 4:
            print("❌ Использование: trello.py show_checklist <card_id> <checklist_id>")
            sys.exit(1)
        card_id = sys.argv[2]
        checklist_id = sys.argv[3]
        show_checklist_items(card_id, checklist_id)

    elif command == 'add-checklist':
        if len(sys.argv) < 5:
            print("❌ Использование: trello.py add-checklist <card_id> 'Название' 'Пункт1' ['Пункт2' ...]")
            sys.exit(1)
        card_id = sys.argv[2]
        checklist_name = sys.argv[3]
        items = sys.argv[4:]
        create_checklist(card_id, checklist_name, items)

    elif command == 'toggle-checkitem':
        if len(sys.argv) < 5:
            print("❌ Использование: trello.py toggle-checkitem <card_id> <item_id> <state>")
            print("State: complete или incomplete")
            sys.exit(1)
        card_id = sys.argv[2]
        item_id = sys.argv[3]
        state = sys.argv[4]
        if state not in ['complete', 'incomplete']:
            print("❌ State должен быть 'complete' или 'incomplete'")
            sys.exit(1)
        toggle_checklist_item(card_id, item_id, state)

    elif command == 'delete-checkitem':
        if len(sys.argv) < 4:
            print("❌ Использование: trello.py delete-checkitem <card_id> <item_id>")
            sys.exit(1)
        card_id = sys.argv[2]
        item_id = sys.argv[3]
        delete_checklist_item(card_id, item_id)

    else:
        print(f"❌ Неизвестная команда: {command}")
