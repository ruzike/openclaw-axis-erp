#!/usr/bin/env python3
"""Сбор данных для утреннего брифинга — вызывается из cron задач.

Использование:
  python3 trello-briefing.py status    — JSON со статусом всех досок
  python3 trello-briefing.py morning   — текстовый утренний отчёт (обёртка trello-report.py)
  python3 trello-briefing.py evening   — текстовый вечерний отчёт
"""
import json
import sys
import requests

CONFIG_PATH = '/home/axis/openclaw/trello-config.json'

with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']


def get_cards(board_name, list_name=None):
    """Получить карточки доски (или конкретной колонки)."""
    board = config['boards'][board_name]
    if list_name:
        list_id = board['lists'][list_name]['id']
        url = f"https://api.trello.com/1/lists/{list_id}/cards"
    else:
        url = f"https://api.trello.com/1/boards/{board['id']}/cards"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'fields': 'name,idList,labels,due,dateLastActivity',
    }
    r = requests.get(url, params=params, timeout=15)
    if r.status_code == 200:
        return r.json()
    print(f"⚠️ Trello API error {r.status_code}: {r.text[:200]}", file=sys.stderr)
    return []


def board_status_json():
    """Возвращает JSON с кратким статусом Production + Strategy."""
    result = {}
    for bname in ('production', 'strategy'):
        board = config['boards'].get(bname)
        if not board:
            continue
        cards = get_cards(bname)
        list_names = {v['id']: v['name'] for v in board['lists'].values()}
        by_list = {}
        for c in cards:
            ln = list_names.get(c['idList'], 'unknown')
            by_list.setdefault(ln, []).append({
                'name': c['name'],
                'labels': [l.get('name', '') for l in c.get('labels', [])],
                'due': c.get('due'),
            })
        result[bname] = by_list
    return result


def print_status():
    data = board_status_json()
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if cmd == 'status':
        print_status()
    elif cmd == 'morning':
        # Делегируем trello-report.py
        import subprocess
        subprocess.run([sys.executable, '/home/axis/openclaw/trello-report.py', 'morning'])
    elif cmd == 'evening':
        import subprocess
        subprocess.run([sys.executable, '/home/axis/openclaw/trello-report.py', 'evening'])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()
