#!/usr/bin/env python3
"""
Remove Trello Webhooks — удаление зарегистрированных webhooks

Использование:
    python3 remove-trello-webhooks.py --all      # удалить все webhooks
    python3 remove-trello-webhooks.py --id XXX   # удалить конкретный webhook
    python3 remove-trello-webhooks.py --list     # показать перед удалением
"""

import json
import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, List

# Конфигурация
CONFIG_FILE = Path("/home/axis/openclaw/trello-config.json")

def load_config() -> Dict:
    if not CONFIG_FILE.exists():
        print(f"❌ Конфиг не найден: {CONFIG_FILE}")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_auth_params(config: Dict) -> Dict[str, str]:
    return {
        "key": config['api']['key'],
        "token": config['api']['token']
    }

def list_webhooks(config: Dict) -> List[Dict]:
    """Получает список всех webhooks"""
    auth = get_auth_params(config)
    token = config['api']['token']
    
    url = f"https://api.trello.com/1/tokens/{token}/webhooks"
    
    try:
        response = requests.get(url, params=auth)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Ошибка получения webhooks: {e}")
        return []

def delete_webhook(config: Dict, webhook_id: str) -> bool:
    """Удаляет webhook по ID"""
    auth = get_auth_params(config)
    
    url = f"https://api.trello.com/1/webhooks/{webhook_id}"
    
    try:
        response = requests.delete(url, params=auth)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"❌ Ошибка удаления: {e}")
        return False

def get_board_name(config: Dict, board_id: str) -> str:
    """Получает имя доски по ID"""
    for key, board in config.get('boards', {}).items():
        if board.get('id') == board_id:
            return board.get('name', key)
    return f"Unknown ({board_id[:8]}...)"

def cmd_list(config: Dict):
    """Показать все webhooks"""
    print("\n📋 Зарегистрированные Trello Webhooks:\n")
    
    webhooks = list_webhooks(config)
    
    if not webhooks:
        print("   (нет webhooks)")
        return webhooks
    
    for i, wh in enumerate(webhooks, 1):
        board_name = get_board_name(config, wh.get('idModel', ''))
        status = "✅" if wh.get('active') else "❌"
        
        print(f"   {i}. {status} {board_name}")
        print(f"      ID: {wh['id']}")
        print(f"      URL: {wh.get('callbackURL', 'N/A')}")
        print()
    
    return webhooks

def cmd_delete_all(config: Dict, dry_run: bool = False):
    """Удалить все webhooks"""
    webhooks = list_webhooks(config)
    
    if not webhooks:
        print("\n✅ Нет webhooks для удаления")
        return
    
    print(f"\n🗑️ {'[DRY RUN] ' if dry_run else ''}Удаление {len(webhooks)} webhooks...\n")
    
    if not dry_run:
        confirm = input("Вы уверены? Введите 'yes' для подтверждения: ")
        if confirm.lower() != 'yes':
            print("Отменено")
            return
    
    deleted = 0
    failed = 0
    
    for wh in webhooks:
        board_name = get_board_name(config, wh.get('idModel', ''))
        webhook_id = wh['id']
        
        if dry_run:
            print(f"   [DRY] Удалил бы: {board_name} ({webhook_id})")
            deleted += 1
        else:
            if delete_webhook(config, webhook_id):
                print(f"   ✅ Удалён: {board_name}")
                deleted += 1
            else:
                print(f"   ❌ Ошибка: {board_name}")
                failed += 1
    
    print(f"\n📊 Итог: удалено {deleted}, ошибок {failed}")

def cmd_delete_one(config: Dict, webhook_id: str):
    """Удалить конкретный webhook"""
    print(f"\n🗑️ Удаление webhook {webhook_id}...")
    
    if delete_webhook(config, webhook_id):
        print("   ✅ Webhook удалён")
    else:
        print("   ❌ Ошибка удаления")

def cmd_delete_inactive(config: Dict):
    """Удалить только неактивные webhooks"""
    webhooks = list_webhooks(config)
    inactive = [wh for wh in webhooks if not wh.get('active')]
    
    if not inactive:
        print("\n✅ Нет неактивных webhooks")
        return
    
    print(f"\n🗑️ Удаление {len(inactive)} неактивных webhooks...\n")
    
    for wh in inactive:
        board_name = get_board_name(config, wh.get('idModel', ''))
        if delete_webhook(config, wh['id']):
            print(f"   ✅ Удалён: {board_name}")
        else:
            print(f"   ❌ Ошибка: {board_name}")

def main():
    parser = argparse.ArgumentParser(
        description="Удаление Trello Webhooks"
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='Показать все webhooks перед удалением'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Удалить все webhooks'
    )
    parser.add_argument(
        '--id',
        type=str,
        help='Удалить webhook по ID'
    )
    parser.add_argument(
        '--inactive',
        action='store_true',
        help='Удалить только неактивные webhooks'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Показать что будет удалено, но не удалять'
    )
    
    args = parser.parse_args()
    
    config = load_config()
    
    if args.list:
        cmd_list(config)
    elif args.all:
        cmd_delete_all(config, dry_run=args.dry_run)
    elif args.id:
        cmd_delete_one(config, args.id)
    elif args.inactive:
        cmd_delete_inactive(config)
    else:
        # По умолчанию показываем список
        cmd_list(config)
        print("💡 Используйте --all для удаления всех webhooks")
        print("   или --id <webhook_id> для удаления конкретного")

if __name__ == '__main__':
    main()
