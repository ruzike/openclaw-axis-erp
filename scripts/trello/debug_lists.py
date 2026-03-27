#!/usr/bin/env python3
"""Debug: Get C3 board lists"""
import json
import requests

# Load config
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

# Get C3 board
board_key = 'c3'
board = config['boards'][board_key]
board_id = board['id']

# Get all lists on the board
board_url = f"https://api.trello.com/1/boards/{board_id}?fields=name&lists=all"
params = {'key': API_KEY, 'token': TOKEN}

print(f"Fetching board info: {board_url}")
r = requests.get(board_url, params=params)
if r.status_code == 200:
    board_data = r.json()
    print(f"Board name: {board_data.get('name')}")
    print(f"Number of lists: {len(board_data.get('lists', []))}")
    print(f"\nLists:")
    for lst in board_data.get('lists', []):
        print(f"  • {lst['name']} (ID: {lst['id']}, closed: {lst.get('closed', False)})")
else:
    print(f"Error: {r.text}")
    print(f"Response: {r.json()}")
