import sys
import json
import requests

with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
CARD_ID = '699ae9a431c8873384959092'
ITEM_NAME = 'Приложить визуализации'

def toggle_item():
    url = f"https://api.trello.com/1/cards/{CARD_ID}/checklists"
    params = {'key': API_KEY, 'token': TOKEN}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(f"Error: {r.text}")
        return

    checklists = r.json()
    for cl in checklists:
        for item in cl['checkItems']:
            if item['name'] == ITEM_NAME:
                print(f"Found item {item['name']} (ID: {item['id']}) in checklist {cl['name']}")
                # Toggle
                url = f"https://api.trello.com/1/cards/{CARD_ID}/checkItem/{item['id']}"
                params = {'key': API_KEY, 'token': TOKEN, 'state': 'complete'}
                r = requests.put(url, params=params)
                if r.status_code == 200:
                    print("✅ Item marked as complete")
                else:
                    print(f"❌ Error toggling item: {r.text}")
                return

if __name__ == "__main__":
    toggle_item()
