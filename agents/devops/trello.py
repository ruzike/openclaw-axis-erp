#!/usr/bin/env python3
"""
Trello Card Manager for Airport Project
Task: Merge all airport-related cards into one main card with checklist
"""

import requests
import json
from datetime import datetime

# Trello API configuration
API_KEY = "5f5f2c9d6b9f4b8b8b8b8b8b"
API_TOKEN = "AgAAAAAtL0XeAQAAAAABH-x0AAAAAAABrAAAAAATL0XeG1hjf4cH9MZVl1YqZG5w1yPw-Qkv"

BASE_URL = "https://api.trello.com/1"

# Board IDs
PRODUCTION_BOARD_ID = "64a4c8b9a4f3d4a4f1a2b3c4"

# Search terms
SEARCH_TERMS = ["аэро", "airport", "Аркалык", "аэропорт"]

# Main card title
MAIN_CARD_TITLE = "Аэропорт Аркалык — Фасад Рабочка"

# Checklist items
CHECKLIST_ITEMS = [
    "Подготовка технического задания",
    "Разработка проекта фасада",
    "Получение согласований",
    "Заказ материалов",
    "Монтажные работы",
    "Финальная приемка"
]


class TrelloManager:
    def __init__(self):
        self.api_key = API_KEY
        self.api_token = API_TOKEN

    def make_request(self, method, params=None):
        """Make a Trello API request"""
        url = f"{BASE_URL}/{method}"
        if params is None:
            params = {}
        params['key'] = self.api_key
        params['token'] = self.api_token
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def search_cards(self, board_id, terms):
        """Find all cards matching search terms"""
        all_cards = []
        for term in terms:
            params = {'idLists': PRODUCTION_BOARD_ID, 'idBoard': board_id}
            if term:
                params['cards'] = f'query={term}'
            try:
                cards = self.make_request('search', params)
                if 'cards' in cards:
                    for card in cards['cards']:
                        # Add the search term for identification
                        card['_search_term'] = term
                        all_cards.append(card)
            except Exception as e:
                print(f"Warning: Search for '{term}' failed: {e}")
        # Remove duplicates (keep first occurrence)
        unique_cards = {}
        for card in all_cards:
            if card['id'] not in unique_cards:
                unique_cards[card['id']] = card
        return list(unique_cards.values())

    def get_list_id_by_name(self, board_id, list_name):
        """Find list ID by name"""
        lists = self.make_request(f'boards/{board_id}/lists')
        for lst in lists:
            if lst['name'].strip() == list_name:
                return lst['id']
        return None

    def find_main_card(self, board_id):
        """Check if main card already exists"""
        cards = self.make_request(f'boards/{board_id}/cards')
        for card in cards:
            if card['name'].strip() == MAIN_CARD_TITLE:
                return card
        return None

    def create_main_card(self, list_id, checklist_id=None):
        """Create the main card"""
        params = {
            'idList': list_id,
            'name': MAIN_CARD_TITLE
        }
        if checklist_id:
            params['idChecklists'] = checklist_id
        card = self.make_request('cards', params)
        print(f"✓ Created main card: {card['name']} (ID: {card['id']})")
        return card

    def create_checklist(self, card_id, items):
        """Create a checklist on a card"""
        checklist = self.make_request(
            'checklists',
            {'idCard': card_id, 'name': 'Подзадачи'}
        )
        print(f"✓ Created checklist: {checklist['name']} (ID: {checklist['id']})")

        # Add items to checklist
        for item in items:
            self.make_request(
                'checklistItems',
                {
                    'idChecklist': checklist['id'],
                    'name': item.strip()
                }
            )
        return checklist['id']

    def delete_card(self, card_id):
        """Delete a card"""
        self.make_request(f'cards/{card_id}', {'closed': True})
        print(f"✓ Deleted card: {card_id}")

    def get_card_details(self, card_id):
        """Get details of a card"""
        return self.make_request(f'cards/{card_id}')

    def main(self):
        """Main execution flow"""
        print("=" * 60)
        print("Trello Airport Card Merger")
        print("=" * 60)

        # Step 1: Find all airport-related cards
        print("\n1. Searching for airport-related cards...")
        airport_cards = self.search_cards(PRODUCTION_BOARD_ID, SEARCH_TERMS)

        if not airport_cards:
            print("⚠ No airport cards found!")
            return

        print(f"\n   Found {len(airport_cards)} card(s):")
        for card in airport_cards:
            print(f"   - {card['name']} (ID: {card['id']})")
            print(f"     Description: {card.get('desc', 'No description')}")

        # Step 2: Find "В работе" list
        print("\n2. Finding 'В работе' list...")
        list_id = self.get_list_id_by_name(PRODUCTION_BOARD_ID, "В работе")
        if not list_id:
            print("⚠ List 'В работе' not found!")
            return
        print(f"   ✓ List ID: {list_id}")

        # Step 3: Check if main card already exists
        print("\n3. Checking for existing main card...")
        existing_card = self.find_main_card(PRODUCTION_BOARD_ID)
        if existing_card:
            print(f"⚠ Main card already exists: {existing_card['name']}")
            print(f"   ID: {existing_card['id']}")
            main_card_id = existing_card['id']
            print("   Skipping card creation. Checklists will be checked.")
        else:
            # Step 4: Create main card
            print("\n4. Creating main card...")
            main_card_id = self.create_main_card(list_id)['id']

            # Step 5: Create checklist
            print("\n5. Creating checklist...")
            checklist_id = self.create_checklist(main_card_id, CHECKLIST_ITEMS)
            print(f"   Checklist items:")
            for item in CHECKLIST_ITEMS:
                print(f"   - {item}")

        # Step 6: Delete old cards (except main card)
        print("\n6. Deleting old airport cards...")
        cards_to_delete = [c for c in airport_cards if c['id'] != main_card_id]
        if cards_to_delete:
            for card in cards_to_delete:
                self.delete_card(card['id'])
        else:
            print("   No old cards to delete")

        # Final report
        print("\n" + "=" * 60)
        print("FINAL REPORT")
        print("=" * 60)
        print(f"Main Card: {MAIN_CARD_TITLE}")
        print(f"Main Card ID: {main_card_id}")
        print(f"Checklist items: {len(CHECKLIST_ITEMS)}")
        print(f"Deleted cards: {len(cards_to_delete)}")
        print(f"Total airport cards processed: {len(airport_cards)}")
        print("=" * 60)

        return {
            'main_card_id': main_card_id,
            'deleted_cards': len(cards_to_delete),
            'total_cards': len(airport_cards)
        }


if __name__ == '__main__':
    manager = TrelloManager()
    result = manager.main()

    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
