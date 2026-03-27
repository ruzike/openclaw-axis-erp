import json
import requests

with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

url = "https://api.trello.com/1/members/me/boards"
params = {'key': API_KEY, 'token': TOKEN}

r = requests.get(url, params=params)
if r.status_code == 200:
    boards = r.json()
    for b in boards:
        print(f"Board: {b['name']} (ID: {b['id']}) URL: {b['shortUrl']}")
else:
    print(f"Error: {r.text}")
