#!/usr/bin/env python3
"""
Find airport cards by listing cards in the production board
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


def get_board_and_list():
    """Get board and list IDs"""
    board = config['boards'][BOARD_NAME]
    if LIST_NAME not in board['lists']:
        print(f"❌ List '{LIST_NAME}' not found on board '{BOARD_NAME}'")
        return None, None
    return board['id'], board['lists'][LIST_NAME]['id']


def list_cards_in_list(list_id):
    """List all cards in a list"""
    params = {'fields': 'name,id,desc'}
    r = trello_request('get', BASE_URL + f'/lists/{list_id}/cards', params)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"❌ Failed to list cards: {r.text}", file=sys.stderr)
        return []


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
    # Check if exists
    existing = find_existing_main_card(board_id)
    if existing:
        print(f"⚠ Main card already exists: {existing['name']}")
        return existing['id']

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
        return card['id']

    checklist = r.json()
    checklist_id = checklist['id']

    # Add items to checklist
    for item in CHECKLIST_ITEMS:
        params = {
            'idChecklist': checklist_id,
            'name': item,
            'pos': 'bottom'
        }
        r = trello_request('post', BASE_URL + f'/checklists/{checklist_id}/checkItems', params)
        if r.status_code != 200:
            print(f"❌ Failed to add item '{item}': {r.text}", file=sys.stderr)

    print(f"✓ Created main card: {card['name']}")
    print(f"✓ Created checklist with {len(CHECKLIST_ITEMS)} items")
    return card['id']


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
    print("Airport Cards Finder")
    print("=" * 60)

    board_id, list_id = get_board_and_list()
    if not board_id or not list_id:
        return {'error': 'Board or list not found'}

    # Check for existing main card
    print(f"\n1. Checking for existing main card...")
    existing_card = find_existing_main_card(board_id)
    if existing_card:
        main_card_id = existing_card['id']
        print(f"✓ Main card exists: {existing_card['name']}")
        print(f"  ID: {main_card_id}")
    else:
        main_card_id = create_main_card(list_id)

    # List cards in the list
    print(f"\n2. Listing all cards in '{LIST_NAME}' list...")
    all_cards = list_cards_in_list(list_id)

    # Filter for airport-related cards
    print(f"\n3. Finding airport-related cards...")
    airport_cards = []
    for card in all_cards:
        card_name = card.get('name', '').lower()
        card_desc = card.get('desc', '').lower()
        # Check search terms
        for term in SEARCH_TERMS:
            term_lower = term.lower()
            if term_lower in card_name or term_lower in card_desc:
                airport_cards.append(card)
                break

    if airport_cards:
        print(f"\n   Found {len(airport_cards)} airport-related card(s):")
        for card in airport_cards:
            print(f"   - {card['name']} (ID: {card['id']})")
    else:
        print("\n   No airport-related cards found in this list.")
        print("   Checking other lists...")

        # Check other lists
        board = config['boards'][BOARD_NAME]
        other_lists = [k for k in board['lists'].keys() if k != LIST_NAME]
        for list_key in other_lists:
            list_id = board['lists'][list_key]['id']
            cards = list_cards_in_list(list_id)
            print(f"\n   Checking list '{board['lists'][list_key]['name']}'...")
            for card in cards:
                card_name = card.get('name', '').lower()
                card_desc = card.get('desc', '').lower()
                found = False
                for term in SEARCH_TERMS:
                    term_lower = term.lower()
                    if term_lower in card_name or term_lower in card_desc:
                        airport_cards.append(card)
                        found = True
                        break
                if found:
                    print(f"   - {card['name']} (ID: {card['id']})")

    # Report
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(f"Main Card: {MAIN_CARD_TITLE}")
    print(f"Main Card ID: {main_card_id}")
    print(f"Airport Cards Found: {len(airport_cards)}")
    print(f"Cards in list: {len(all_cards)}")
    print("=" * 60)

    return {
        'main_card_id': main_card_id,
        'airport_cards_found': len(airport_cards),
        'airport_cards': [c['id'] for c in airport_cards],
        'all_cards': [c['id'] for c in all_cards]
    }


if __name__ == '__main__':
    result = main()
    print(json.dumps(result, indent=2, ensure_ascii=False))
