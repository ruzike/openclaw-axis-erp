import json
import requests
import sys

BOARD_ID = '697ea1c3b95f7266bd54f96b'

with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists"
params = {'key': API_KEY, 'token': TOKEN}

r = requests.get(url, params=params)
if r.status_code == 200:
    lists = r.json()
    print("Список колонок:")
    for l in lists:
        print(f"ID: {l['id']} Name: {l['name']}")
