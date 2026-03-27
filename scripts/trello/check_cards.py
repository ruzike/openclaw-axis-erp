#!/usr/bin/env python3
import json
import requests

# Load config
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

# Search for cards with 'airport arkalys' in the name
boards_to_search = ['production', 'ced_supervision', 'c3']
found_cards = []

for board_key in boards_to_search:
    board = config['boards'][board_key]
    # Get all lists on this board
    board_url = f'https://api.trello.com/1/boards/{board["id"]}'
    params = {'key': API_KEY, 'token': TOKEN, 'fields': 'name'}
    r = requests.get(board_url, params=params)
    if r.status_code == 200:
        board_data = r.json()
        lists_data = board_data.get('lists', [])
        print(f'\nSearching in {board_key}...')
        for lst in lists_data:
            # Search cards in this list
            cards_url = f'https://api.trello.com/1/lists/{lst["id"]}/cards'
            r = requests.get(cards_url, params={'key': API_KEY, 'token': TOKEN, 'fields': 'name,id,shortUrl'})
            if r.status_code == 200:
                cards = r.json()
                for card in cards:
                    if 'airport' in card['name'].lower() or 'аркалык' in card['name'].lower():
                        found_cards.append({'board': board_key, 'list': lst['name'], 'card': card})
                        print(f"  Found: {card['name']} ({card['id']}) - {lst['name']}")

if not found_cards:
    print('No airport arkalys cards found.')
