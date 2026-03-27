import json
import requests
from datetime import datetime

with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
BOARD_KEY = 'c3'
LIST_ID = config['boards'][BOARD_KEY]['lists']['inProgress']['id']

# Create reverse lookup for members
member_map = {v['trello_id']: {'name': k, 'tg': v['telegram_id']} for k, v in config['members'].items()}

url = f"https://api.trello.com/1/lists/{LIST_ID}/cards"
params = {'key': API_KEY, 'token': TOKEN, 'fields': 'name,due,idMembers,shortUrl'}

r = requests.get(url, params=params)
cards = r.json()

tasks_by_user = {}

for card in cards:
    due = card.get('due')
    if due:
        due_date = datetime.strptime(due, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d.%m.%Y')
    else:
        due_date = 'Без дедлайна'
        
    members = card.get('idMembers', [])
    if not members:
        # Unassigned
        tasks_by_user.setdefault('Unassigned', []).append({'name': card['name'], 'due': due_date})
    else:
        for m_id in members:
            u_info = member_map.get(m_id, {'name': 'Unknown', 'tg': None})
            tasks_by_user.setdefault(u_info['name'], []).append({'name': card['name'], 'due': due_date, 'tg': u_info['tg']})

for user, tasks in tasks_by_user.items():
    print(f"\n👤 Исполнитель: {user}")
    for t in tasks:
        print(f"  - {t['name']} (Дедлайн: {t['due']})")
        if t.get('tg'):
            print(f"    TG: {t['tg']}")
