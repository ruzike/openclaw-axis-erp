import json
import requests

CONFIG_PATH = '/home/axis/openclaw/trello-config.json'
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

def get_cards(board_name, list_name):
    try:
        if board_name not in config['boards']: return []
        board = config['boards'][board_name]
        if list_name not in board['lists']: return []
        list_id = board['lists'][list_name]['id']
        r = requests.get(f"https://api.trello.com/1/lists/{list_id}/cards", params={'key': API_KEY, 'token': TOKEN})
        if r.status_code == 200: return r.json()
    except Exception as e:
        pass
    return []

print("=== ДОН (DONE) ===")
print("C1/C2:")
for c in get_cards('production', 'done'): print("-", c['name'])
print("C3:")
for c in get_cards('c3', 'done'): print("-", c['name'])

print("\n=== В РАБОТЕ (IN PROGRESS) / ЗАСТРЯЛО ===")
print("C1/C2:")
for c in get_cards('production', 'inProgress'): print("-", c['name'])
print("C3:")
for c in get_cards('c3', 'inProgress'): print("-", c['name'])
print("Стратегия (Внедряю):")
for c in get_cards('strategy', 'внедряю'): print("-", c['name'])

print("\n=== БЭКЛОГ / НА СЛЕД. НЕДЕЛЮ ===")
print("C1/C2 Бэклог:")
for c in get_cards('production', 'backlog')[:5]: print("-", c['name'])
print("C3 Бэклог:")
for c in get_cards('c3', 'backlog')[:5]: print("-", c['name'])
print("Стратегия (Месяц):")
for c in get_cards('strategy', 'этот_месяц')[:5]: print("-", c['name'])

