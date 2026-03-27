import json
import requests
import sys

BOARD_KEY = 'production'
DEADLINE = '2026-02-27T12:00:00.000Z' # Friday

with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
BOARD_ID = config['boards'][BOARD_KEY]['id']

lists = config['boards'][BOARD_KEY]['lists']
ACTIVE_LISTS = ['queue', 'inProgress']

print(f"🗓 Setting Deadline to {DEADLINE} for all cards on {BOARD_KEY}...")

for list_key in ACTIVE_LISTS:
    if list_key not in lists:
        continue
    
    list_id = lists[list_key]['id']
    
    url = f"https://api.trello.com/1/lists/{list_id}/cards"
    params = {'key': API_KEY, 'token': TOKEN, 'fields': 'name,shortUrl'}
    
    r = requests.get(url, params=params)
    cards = r.json()
    
    for card in cards:
        print(f"⏳ Updating: {card['name']}...")
        
        url_update = f"https://api.trello.com/1/cards/{card['id']}"
        params_update = {
            'key': API_KEY, 
            'token': TOKEN, 
            'due': DEADLINE
        }
        
        r_up = requests.put(url_update, params=params_update)
        if r_up.status_code == 200:
            print(f"✅ Deadline set! 🔗 {card['shortUrl']}")
        else:
            print(f"❌ Error setting deadline for {card['name']}: {r_up.text}")

print("\n✅ Batch update complete!")
