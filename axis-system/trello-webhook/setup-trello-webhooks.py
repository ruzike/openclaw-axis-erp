#!/usr/bin/env python3
"""
Setup Trello Webhooks — регистрация webhook на досках Trello

Регистрирует webhooks для всех досок из trello-config.json.
Требует публичный HTTPS URL (через Cloudflare Tunnel, ngrok и т.д.)

Использование:
    python3 setup-trello-webhooks.py --url https://your-tunnel.trycloudflare.com
    python3 setup-trello-webhooks.py --list   # показать текущие webhooks
    python3 setup-trello-webhooks.py --check  # проверить статус
"""

import json
import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Optional

# Конфигурация
CONFIG_FILE = Path("/home/axis/openclaw/trello-config.json")
WEBHOOK_ENDPOINT = "/webhook/trello"

# Загрузка конфигурации
def load_config() -> Dict:
    if not CONFIG_FILE.exists():
        print(f"❌ Конфиг не найден: {CONFIG_FILE}")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_auth_params(config: Dict) -> Dict[str, str]:
    """Возвращает параметры авторизации для Trello API"""
    return {
        "key": config['api']['key'],
        "token": config['api']['token']
    }

def list_webhooks(config: Dict) -> List[Dict]:
    """Получает список всех зарегистрированных webhooks"""
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

def create_webhook(config: Dict, board_id: str, callback_url: str, description: str) -> Optional[Dict]:
    """Создаёт webhook для доски"""
    auth = get_auth_params(config)
    
    url = "https://api.trello.com/1/webhooks"
    
    payload = {
        **auth,
        "callbackURL": callback_url,
        "idModel": board_id,
        "description": description,
        "active": True
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            error = response.json() if response.text else {"message": response.text}
            print(f"❌ Ошибка создания webhook: {error}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Сетевая ошибка: {e}")
        return None

def delete_webhook(config: Dict, webhook_id: str) -> bool:
    """Удаляет webhook по ID"""
    auth = get_auth_params(config)
    
    url = f"https://api.trello.com/1/webhooks/{webhook_id}"
    
    try:
        response = requests.delete(url, params=auth)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"❌ Ошибка удаления webhook: {e}")
        return False

def get_boards_to_monitor(config: Dict) -> List[Dict]:
    """Возвращает список досок для мониторинга"""
    boards = []
    seen_ids = set()  # Избегаем дубликатов (c1c2 = production)
    
    for key, board in config.get('boards', {}).items():
        if 'id' in board and board['id'] not in seen_ids:
            boards.append({
                'key': key,
                'id': board['id'],
                'name': board.get('name', key)
            })
            seen_ids.add(board['id'])
    
    return boards

def cmd_list(config: Dict):
    """Команда: показать текущие webhooks"""
    print("\n📋 Текущие Trello Webhooks:\n")
    
    webhooks = list_webhooks(config)
    
    if not webhooks:
        print("   (нет зарегистрированных webhooks)")
        return
    
    for wh in webhooks:
        status = "✅ active" if wh.get('active') else "❌ inactive"
        print(f"   ID: {wh['id']}")
        print(f"   Model: {wh.get('idModel', 'N/A')}")
        print(f"   URL: {wh.get('callbackURL', 'N/A')}")
        print(f"   Description: {wh.get('description', 'N/A')}")
        print(f"   Status: {status}")
        print()

def cmd_setup(config: Dict, base_url: str, force: bool = False):
    """Команда: установить webhooks на все доски"""
    if not base_url:
        print("❌ Укажите --url с публичным HTTPS URL")
        print("   Пример: python3 setup-trello-webhooks.py --url https://xxx.trycloudflare.com")
        sys.exit(1)
    
    # Убираем trailing slash
    base_url = base_url.rstrip('/')
    callback_url = f"{base_url}{WEBHOOK_ENDPOINT}"
    
    print(f"\n🔧 Настройка Trello Webhooks")
    print(f"   Callback URL: {callback_url}\n")
    
    # Проверяем доступность endpoint
    print("1️⃣ Проверка доступности endpoint...")
    try:
        # HEAD запрос как делает Trello
        response = requests.head(callback_url, timeout=10)
        if response.status_code != 200:
            print(f"   ⚠️ Endpoint вернул {response.status_code} (ожидается 200)")
            print("   Убедитесь, что сервер запущен и туннель работает")
            if not force:
                confirm = input("   Продолжить? (y/N): ")
                if confirm.lower() != 'y':
                    sys.exit(1)
        else:
            print("   ✅ Endpoint доступен")
    except requests.RequestException as e:
        print(f"   ❌ Endpoint недоступен: {e}")
        print("   Запустите сервер и туннель перед установкой webhooks")
        sys.exit(1)
    
    # Получаем существующие webhooks
    print("\n2️⃣ Проверка существующих webhooks...")
    existing = list_webhooks(config)
    existing_models = {wh['idModel'] for wh in existing}
    
    # Получаем доски
    boards = get_boards_to_monitor(config)
    print(f"   Найдено {len(boards)} досок для мониторинга")
    
    # Создаём webhooks
    print("\n3️⃣ Создание webhooks...\n")
    
    created = 0
    skipped = 0
    failed = 0
    
    for board in boards:
        board_id = board['id']
        board_name = board['name']
        
        if board_id in existing_models:
            print(f"   ⏭️ {board_name} — уже есть webhook")
            skipped += 1
            continue
        
        description = f"AXIS Webhook: {board_name}"
        
        print(f"   🔄 {board_name}...")
        result = create_webhook(config, board_id, callback_url, description)
        
        if result:
            print(f"   ✅ {board_name} — webhook создан (ID: {result['id']})")
            created += 1
        else:
            print(f"   ❌ {board_name} — ошибка создания")
            failed += 1
    
    # Итог
    print(f"\n📊 Итог:")
    print(f"   Создано: {created}")
    print(f"   Пропущено (уже есть): {skipped}")
    print(f"   Ошибок: {failed}")

def cmd_check(config: Dict):
    """Команда: проверить статус webhooks"""
    print("\n🔍 Проверка статуса Trello Webhooks\n")
    
    webhooks = list_webhooks(config)
    boards = get_boards_to_monitor(config)
    
    # Создаём маппинг id -> board
    board_map = {b['id']: b for b in boards}
    webhook_map = {wh['idModel']: wh for wh in webhooks}
    
    print("Доски и их webhooks:\n")
    
    for board in boards:
        board_id = board['id']
        board_name = board['name']
        
        if board_id in webhook_map:
            wh = webhook_map[board_id]
            status = "✅" if wh.get('active') else "⚠️"
            print(f"   {status} {board_name}")
            print(f"      URL: {wh.get('callbackURL', 'N/A')}")
            print(f"      Active: {wh.get('active', False)}")
        else:
            print(f"   ❌ {board_name} — webhook НЕ установлен")
        print()

def main():
    parser = argparse.ArgumentParser(
        description="Управление Trello Webhooks для AXIS System"
    )
    
    parser.add_argument(
        '--url',
        type=str,
        help='Публичный HTTPS URL для webhook (например, https://xxx.trycloudflare.com)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='Показать все зарегистрированные webhooks'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Проверить статус webhooks для всех досок'
    )
    parser.add_argument(
        '--board',
        type=str,
        help='Установить webhook только для указанной доски (ключ из конфига)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Не спрашивать подтверждение'
    )
    
    args = parser.parse_args()
    
    # Загружаем конфиг
    config = load_config()
    
    # Выполняем команду
    if args.list:
        cmd_list(config)
    elif args.check:
        cmd_check(config)
    elif args.url:
        cmd_setup(config, args.url, force=args.force)
    else:
        parser.print_help()
        print("\n💡 Примеры:")
        print("   python3 setup-trello-webhooks.py --list")
        print("   python3 setup-trello-webhooks.py --check")
        print("   python3 setup-trello-webhooks.py --url https://your-tunnel.trycloudflare.com")

if __name__ == '__main__':
    main()
