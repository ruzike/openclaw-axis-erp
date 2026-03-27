#!/usr/bin/env python3
"""
Merge airport cards into one main card with checklist
"""

import sys
import json
import requests
import time

# Load config
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

BASE_URL = "https://api.trello.com/1"

# Configuration
BOARD_NAME = "production"
LIST_NAME = "inProgress"
MAIN_CARD_TITLE = "Аэропорт Аркалык — Фасад Рабочка"
SEARCH_TERMS = ["аэро", "airport", "Аркалык", "аэропорт"]
CHECKLIST_ITEMS = [
    "Подготовка технического задания",
    "Разработка проекта фасада",
    "Получение согласований",
    "Заказ материалов",
    "Монтажные работы",
    "Финальная приемка"
]


def trello_request(method, url, params=None, max_retries=4, **kwargs):
    """Wrapper with rate limit handling"""
    if params is None:
        params = {}
    params.setdefault('key', API_KEY)
    params.setdefault('token', TOKEN)

    for attempt in range(max_retries):
        r = getattr(requests, method)(url, params=params, **kwargs)
        if r.status_code == 429:
            retry_after = int(r.headers.get('Retry-After', 10))
            wait = retry_after + attempt * 5
            print(f"⏳ Rate limit hit — waiting {wait}s (attempt {attempt+1}/{max_retries})...", file=sys.stderr)
            time.sleep(wait)
            continue
        return r
    return r


def find_board_and_list():
    """Get board and list IDs"""
    board = config['boards'][BOARD_NAME]
    if LIST_NAME not in board['lists']:
        print(f"❌ List '{LIST_NAME}' not found on board '{BOARD_NAME}'")
        return None, None
    return board['id'], board['lists'][LIST_NAME]['id']


def search_airport_cards(board_id, terms):
    """Find all airport-related cards"""
    all_cards = []
    for term in terms:
        params = {
            'idBoard': board_id,
            'cards': f'query={term}'
        }
        r = trello_request('get', BASE_URL + '/search', params)
        if r.status_code == 200:
            data = r.json()
            if 'cards' in data:
                for card in data['cards']:
                    card['_search_term'] = term
                    all_cards.append(card)
        else:
            print(f"⚠ Search for '{term}' failed: {r.status_code} {r.text}", file=sys.stderr)

    # Remove duplicates
    unique_cards = {}
    for card in all_cards:
        if card['id'] not in unique_cards:
            unique_cards[card['id']] = card
    return list(unique_cards.values())


def find_existing_main_card(board_id):
    """Check if main card already exists"""
    r = trello_request('get', BASE_URL + f'/boards/{board_id}/cards')
    if r.status_code == 200:
        cards = r.json()
        for card in cards:
            if card['name'].strip() == MAIN_CARD_TITLE:
                return card
    return None


def create_main_card(list_id):
    """Create main card with checklist"""
    # Create card
    params = {
        'idList': list_id,
        'name': MAIN_CARD_TITLE
    }
    r = trello_request('post', BASE_URL + '/cards', params)
    if r.status_code != 200:
        print(f"❌ Failed to create card: {r.text}", file=sys.stderr)
        return None
    card = r.json()

    # Create checklist
    checklist_name = 'Подзадачи'
    params = {
        'idCard': card['id'],
        'name': checklist_name
    }
    r = trello_request('post', BASE_URL + '/checklists', params)
    if r.status_code != 200:
        print(f"❌ Failed to create checklist: {r.text}", file=sys.stderr)
        return card  # Return card even if checklist failed

    checklist = r.json()
    checklist_id = checklist['id']

    # Add items to checklist
    for item in CHECKLIST_ITEMS:
        params = {
            'idChecklist': checklist_id,
            'name': item,
            'pos': 'bottom'
        }
        r = trello_request('post', BASE_URL + '/checklists/' + checklist_id + '/checkItems', params)
        if r.status_code != 200:
            print(f"❌ Failed to add item '{item}': {r.text}", file=sys.stderr)

    print(f"✓ Created main card: {card['name']}")
    print(f"✓ Created checklist with {len(CHECKLIST_ITEMS)} items")
    return card


def delete_card(card_id):
    """Close/delete a card"""
    params = {'closed': True}
    r = trello_request('put', BASE_URL + f'/cards/{card_id}', params)
    if r.status_code == 200:
        print(f"✓ Deleted card: {card_id}")
        return True
    else:
        print(f"❌ Failed to delete card {card_id}: {r.text}", file=sys.stderr)
        return False


def main():
    print("=" * 60)
    print("Airport Cards Merger")
    print("=" * 60)

    # Get board and list
    board_id, list_id = find_board_and_list()
    if not board_id or not list_id:
        return {'error': 'Board or list not found'}

    # Find existing main card
    print(f"\n1. Checking for existing main card...")
    existing_card = find_existing_main_card(board_id)
    if existing_card:
        print(f"⚠ Main card already exists: {existing_card['name']}")
        main_card_id = existing_card['id']
        print(f"   ID: {main_card_id}")
    else:
        print(f"\n2. Creating main card...")
        main_card = create_main_card(list_id)
        if not main_card:
            return {'error': 'Failed to create main card'}
        main_card_id = main_card['id']

    # Search for airport cards
    print(f"\n3. Searching for airport-related cards...")
    airport_cards = search_airport_cards(board_id, SEARCH_TERMS)

    if not airport_cards:
        print("⚠ No airport cards found!")
        return {'main_card_id': main_card_id, 'airport_cards_found': 0, 'deleted_cards': 0}

    print(f"\n   Found {len(airport_cards)} card(s):")
    for card in airport_cards:
        print(f"   - {card['name']} (ID: {card['id']})")

    # Delete old cards
    print(f"\n4. Deleting old cards (excluding main card)...")
    cards_to_delete = [c for c in airport_cards if c['id'] != main_card_id]
    deleted_count = 0
    for card in cards_to_delete:
        if delete_card(card['id']):
            deleted_count += 1

    # Report
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(f"Main Card: {MAIN_CARD_TITLE}")
    print(f"Main Card ID: {main_card_id}")
    print(f"Checklist Items: {len(CHECKLIST_ITEMS)}")
    print(f"Airport Cards Found: {len(airport_cards)}")
    print(f"Deleted Cards: {deleted_count}")
    print("=" * 60)

    return {
        'main_card_id': main_card_id,
        'airport_cards_found': len(airport_cards),
        'deleted_cards': deleted_count,
        'total_processed': len(airport_cards)
    }


if __name__ == '__main__':
    result = main()
    print(json.dumps(result, indent=2, ensure_ascii=False))
