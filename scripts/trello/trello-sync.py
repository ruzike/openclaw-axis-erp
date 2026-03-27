#!/usr/bin/env python3
"""Синхронизация состояния Trello и обработка уведомлений"""
import json
import os
from datetime import datetime

STATE_FILE = '/home/axis/openclaw/.trello-state.json'
NOTIFICATION_FILE = '/home/axis/openclaw/.trello-notifications.jsonl'

def load_state():
    """Загрузить состояние доски"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'cards': {}, 'last_update': None, 'changes': []}

def get_pending_notifications():
    """Получить непрочитанные уведомления"""
    if not os.path.exists(NOTIFICATION_FILE):
        return []
    
    notifications = []
    with open(NOTIFICATION_FILE, 'r') as f:
        for line in f:
            if line.strip():
                notifications.append(json.loads(line))
    
    # Очистить файл после чтения
    if notifications:
        os.remove(NOTIFICATION_FILE)
    
    return notifications

def get_board_summary():
    """Получить краткую сводку по доске"""
    state = load_state()
    cards = state.get('cards', {})
    
    summary = {
        'total': len(cards),
        'by_list': {}
    }
    
    for card_id, card_data in cards.items():
        list_name = card_data.get('list', 'Unknown')
        if list_name not in summary['by_list']:
            summary['by_list'][list_name] = []
        summary['by_list'][list_name].append(card_data['name'])
    
    return summary

def get_recent_changes(hours=24):
    """Получить изменения за последние N часов"""
    state = load_state()
    changes = state.get('changes', [])
    
    recent = []
    now = datetime.now()
    
    for change in changes:
        change_time = datetime.fromisoformat(change['timestamp'])
        hours_ago = (now - change_time).total_seconds() / 3600
        
        if hours_ago <= hours:
            recent.append(change)
    
    return recent

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 trello-sync.py notifications  # Получить уведомления")
        print("  python3 trello-sync.py summary         # Сводка по доске")
        print("  python3 trello-sync.py changes [hours] # Изменения за период")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'notifications':
        notifications = get_pending_notifications()
        if notifications:
            print(json.dumps(notifications, ensure_ascii=False, indent=2))
        else:
            print("[]")
    
    elif command == 'summary':
        summary = get_board_summary()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    elif command == 'changes':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        changes = get_recent_changes(hours)
        print(json.dumps(changes, ensure_ascii=False, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
