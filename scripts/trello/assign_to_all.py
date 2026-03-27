import json
import requests
import sys

BOARD_KEY = 'production' # C1C2
MEMBER_NAME = 'ruslan'

with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
MEMBER_ID = config['members'][MEMBER_NAME]['trello_id']
BOARD_ID = config['boards'][BOARD_KEY]['id']

# Get lists
lists = config['boards'][BOARD_KEY]['lists']
ACTIVE_LISTS = ['queue', 'inProgress', 'review', 'corrections'] # Active lists

print(f"🔍 Scanning board {BOARD_KEY} ({BOARD_ID})...")

TOTAL_CARDS = 0
ASSIGNED = 0
NO_DEADLINE = []

for list_key in ACTIVE_LISTS:
    if list_key not in lists:
        continue
    
    list_id = lists[list_key]['id']
    list_name = lists[list_key]['name']
    
    url = f"https://api.trello.com/1/lists/{list_id}/cards"
    params = {'key': API_KEY, 'token': TOKEN, 'fields': 'name,idMembers,due,shortUrl'}
    
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(f"❌ Error getting cards for list {list_name}: {r.text}")
        continue
        
    cards = r.json()
    for card in cards:
        TOTAL_CARDS += 1
        
        # 1. Assign Member if not present
        if MEMBER_ID not in card['idMembers']:
            print(f"👤 Assigning {MEMBER_NAME} to: {card['name']}")
            url_assign = f"https://api.trello.com/1/cards/{card['id']}/idMembers"
            params_assign = {'key': API_KEY, 'token': TOKEN, 'value': MEMBER_ID}
            r_assign = requests.post(url_assign, params=params_assign)
            if r_assign.status_code == 200:
                ASSIGNED += 1
                
        # 2. Check Deadline
        if not card.get('due'):
            NO_DEADLINE.append(f"🔴 {card['name']} (List: {list_name}) - {card['shortUrl']}")

print(f"\n📊 SUMMARY:")
print(f"Total Cards Scanned: {TOTAL_CARDS}")
print(f"Newly Assigned: {ASSIGNED}")
print(f"Cards WITHOUT Deadline: {len(NO_DEADLINE)}")

if NO_DEADLINE:
    print("\n⚠️ Cards missing deadline:")
    for m in NO_DEADLINE:
        print(m)
else:
    print("\n✅ All cards have deadlines!")
