#!/usr/bin/env python3
"""
Trello → projects-history → ChromaDB
Автоматически сохраняет закрытые карточки Trello в projects-history
и индексирует их в ChromaDB.

Запуск: python3 trello-to-history.py
Cron: вызывается из trello-webhook-server.py при перемещении в "Готово"
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CONFIG_FILE = "/home/axis/openclaw/trello-config.json"
HISTORY_DIR = "/home/axis/openclaw/projects-history/2026"
TEMPLATE = "/home/axis/openclaw/projects-history/_template.md"
INDEX_SCRIPT = "/home/axis/openclaw/axis-system/semantic-index.py"

# Trello API
import urllib.request
import urllib.parse

def get_trello_creds():
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    return config['api']['key'], config['api']['token']

def get_card_details(card_id):
    key, token = get_trello_creds()
    url = f"https://api.trello.com/1/cards/{card_id}?key={key}&token={token}&fields=name,desc,due,dateLastActivity,labels,idMembers,shortUrl&members=true&member_fields=username,fullName"
    resp = urllib.request.urlopen(url, timeout=15)
    return json.loads(resp.read())

def save_to_history(card_data, board_name, list_name):
    """Сохраняет карточку как файл в projects-history"""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    name = card_data.get('name', 'Unknown')
    card_id = card_data.get('id', '')[:8]
    safe_name = "".join(c if c.isalnum() or c in ' -_' else '' for c in name)[:50].strip().replace(' ', '-').lower()
    
    filename = f"axis-{card_id}-{safe_name}.md"
    filepath = os.path.join(HISTORY_DIR, filename)
    
    if os.path.exists(filepath):
        print(f"⏭️ Уже существует: {filename}")
        return filepath
    
    # Формируем markdown
    members = ', '.join(m.get('fullName', m.get('username', '?')) for m in card_data.get('members', []))
    labels = ', '.join(l.get('name', '') for l in card_data.get('labels', []) if l.get('name'))
    due = card_data.get('due', 'не указано')
    desc = card_data.get('desc', '')
    
    content = f"""# {name}

**Дата сдачи:** {due}
**Доска:** {board_name}
**Список:** {list_name}
**Метки:** {labels or 'нет'}
**Участники:** {members or 'не назначены'}
**Trello:** {card_data.get('shortUrl', '')}

## Описание
{desc or '_Описание не заполнено_'}

## Итог
Карточка закрыта {datetime.now().strftime('%Y-%m-%d')}.
"""
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Сохранено: {filename}")
    return filepath

def index_to_chromadb():
    """Запускает инкрементальную индексацию"""
    try:
        result = subprocess.run(
            ["python3", INDEX_SCRIPT],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, 'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', '')}
        )
        if result.returncode == 0:
            print("✅ ChromaDB обновлён")
        else:
            print(f"⚠️ Индексация: {result.stderr[:100]}")
    except Exception as e:
        print(f"❌ Индексация: {e}")

def process_card(card_id, board_name="Unknown", list_name="Готово"):
    """Основная функция: карточка → history → ChromaDB"""
    print(f"📦 Обработка карточки {card_id}...")
    
    card = get_card_details(card_id)
    filepath = save_to_history(card, board_name, list_name)
    index_to_chromadb()
    
    return filepath

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 trello-to-history.py <card_id> [board_name] [list_name]")
        sys.exit(1)
    
    card_id = sys.argv[1]
    board = sys.argv[2] if len(sys.argv) > 2 else "Unknown"
    lst = sys.argv[3] if len(sys.argv) > 3 else "Готово"
    
    process_card(card_id, board, lst)
