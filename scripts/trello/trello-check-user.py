#!/usr/bin/env python3
"""
Скрипт проверки загрузки сотрудников по всем доскам Trello.
Используется Ops агентом перед отправкой сообщений "задач нет".
"""
import json
import requests
import sys
import time

# Загружаем конфиг
CONFIG_PATH = '/home/axis/openclaw/trello-config.json'
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
MEMBERS = config['members']

# Списки, которые считаются "завершенными" или "отмененными"
DONE_KEYWORDS = ['done', 'готово', 'внедрено', 'не актуально', 'архив', 'archive', 'notrelevant']

def is_done_list(list_name):
    """Проверяет, является ли колонка 'завершенной'"""
    norm = list_name.lower().replace(' ', '').replace('_', '')
    for kw in DONE_KEYWORDS:
        if kw.lower() in norm:
            return True
    return False

def get_boards():
    """Возвращает список уникальных ID досок из конфига"""
    boards = {}
    for key, b in config['boards'].items():
        if b['id'] not in boards:
            boards[b['id']] = b['name']
    return boards

def get_cards_on_board(board_id):
    """Получает все карточки с доски (сразу с members)"""
    url = f"https://api.trello.com/1/boards/{board_id}/cards"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'filter': 'visible',
        'members': 'true' 
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return r.json()
    return []

def get_list_name(board_id, list_id):
    """Получает имя колонки (кэшируя запросы, если нужно, но пока просто ищем в конфиге)"""
    # Пробуем найти в конфиге
    for b_key, b_val in config['boards'].items():
        if b_val['id'] == board_id:
            for l_key, l_val in b_val['lists'].items():
                if l_val['id'] == list_id:
                    return l_val['name']
    
    # Если нет в конфиге, запрашиваем API
    url = f"https://api.trello.com/1/lists/{list_id}"
    params = {'key': API_KEY, 'token': TOKEN}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return r.json()['name']
    return "Unknown List"

def check_user_load(target_member_key=None):
    """Проверяет загрузку пользователя (или всех)"""
    
    # Определяем кого ищем
    targets = []
    if target_member_key:
        # Ищем по ключу (miras) или имени (Miras)
        found = False
        for m_key, m_val in MEMBERS.items():
            if m_key.lower() == target_member_key.lower() or m_val.get('username', '').lower() == target_member_key.lower():
                targets.append((m_key, m_val['trello_id'], m_val.get('username')))
                found = True
                break
        if not found:
            print(f"❌ Пользователь '{target_member_key}' не найден в конфиге.")
            sys.exit(1)
    else:
        # Всех из конфига
        for m_key, m_val in MEMBERS.items():
            targets.append((m_key, m_val['trello_id'], m_val.get('username')))

    print(f"🔍 Проверка загрузки для: {', '.join([t[0] for t in targets])}...\n")

    boards = get_boards()
    user_tasks = {t[1]: [] for t in targets} # trello_id -> list of tasks

    # Проходим по всем доскам
    for board_id, board_name in boards.items():
        cards = get_cards_on_board(board_id)
        
        # Кэш имен колонок для этой доски
        list_names = {}

        for card in cards:
            # Пропускаем, если никого из targets нет в карточке
            card_members = card['idMembers']
            relevant_users = [t for t in targets if t[1] in card_members]
            
            if not relevant_users:
                continue

            # Получаем имя колонки
            list_id = card['idList']
            if list_id not in list_names:
                list_names[list_id] = get_list_name(board_id, list_id)
            
            list_name = list_names[list_id]

            # Если колонка "Готово" - пропускаем
            if is_done_list(list_name):
                continue

            # Сохраняем задачу
            task_info = {
                'board': board_name,
                'list': list_name,
                'name': card['name'],
                'url': card['shortUrl']
            }

            for u in relevant_users:
                user_tasks[u[1]].append(task_info)

    # Вывод результатов
    for t in targets:
        m_key, m_id, m_user = t
        tasks = user_tasks[m_id]
        
        print(f"👤 {m_key.upper()} ({m_user})")
        if not tasks:
            print("   ✅ Задач в работе нет (свободен)")
        else:
            print(f"   🔥 В работе: {len(tasks)} задач")
            for task in tasks:
                print(f"   • [{task['board']} | {task['list']}] {task['name']}")
                print(f"     🔗 {task['url']}")
        print("")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else None
    check_user_load(target)
