import sys
import json
import requests

config_path = '/home/axis/openclaw/trello-config.json'

def move_card(card_id, target_board_key, target_list_key):
    with open(config_path, 'r') as f:
        config = json.load(f)

    api_key = config['api']['key']
    token = config['api']['token']

    # Get target board ID
    target_board = config['boards'].get(target_board_key)
    if not target_board:
        print(f"❌ Target board '{target_board_key}' not found in config.")
        return

    target_board_id = target_board['id']

    # Get target list ID
    target_list = target_board['lists'].get(target_list_key)
    if not target_list:
        print(f"❌ Target list '{target_list_key}' not found on board '{target_board_key}'.")
        return

    target_list_id = target_list['id']

    print(f"📦 Moving card {card_id}...")
    print(f"➡️  To Board: {target_board['name']} ({target_board_key})")
    print(f"➡️  To List: {target_list['name']} ({target_list_key})")

    url = f"https://api.trello.com/1/cards/{card_id}"
    params = {
        'key': api_key,
        'token': token,
        'idBoard': target_board_id,
        'idList': target_list_id
    }

    r = requests.put(url, params=params)

    if r.status_code == 200:
        card = r.json()
        print(f"✅ Success! Card moved.")
        print(f"🔗 {card['shortUrl']}")
    else:
        print(f"❌ Error moving card: {r.status_code} {r.text}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 move_card_cross_board.py <card_id> <target_board_key> <target_list_key>")
        sys.exit(1)
    
    move_card(sys.argv[1], sys.argv[2], sys.argv[3])
