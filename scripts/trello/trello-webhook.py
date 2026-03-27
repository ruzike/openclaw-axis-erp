#!/usr/bin/env python3
"""Trello Webhook Server (без внешних зависимостей)"""
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import threading

# Загрузка конфига
with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
BOARD_ID = config['board']['id']

# Пути к файлам
STATE_FILE = '/home/axis/openclaw/.trello-state.json'
LOG_FILE = '/home/axis/openclaw/trello-webhook.log'
NOTIFICATION_FILE = '/home/axis/openclaw/.trello-notifications.jsonl'

def log(msg):
    """Логирование событий"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass
    print(f"[{timestamp}] {msg}")

def load_state():
    """Загрузить текущее состояние"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'cards': {},
        'last_update': None,
        'changes': []
    }

def save_state(state):
    """Сохранить состояние"""
    state['last_update'] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def is_critical_card(card_name):
    """Определить критичность карточки"""
    critical_keywords = ['🔥', 'КРИТИЧЕСКИЙ', 'критический', 'критично', 'срочно', 'СРОЧНО']
    return any(kw in card_name for kw in critical_keywords)

def notify_telegram(message):
    """Отправить уведомление в Telegram (через очередь для heartbeat)"""
    notification = {
        'timestamp': datetime.now().isoformat(),
        'message': message
    }
    with open(NOTIFICATION_FILE, 'a') as f:
        f.write(json.dumps(notification, ensure_ascii=False) + '\n')
    log(f"Notification queued: {message[:50]}...")

class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Отключаем дефолтное логирование запросов"""
        pass
    
    def do_HEAD(self):
        """Trello webhook verification"""
        log("Webhook verification (HEAD)")
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        """Обработка Trello webhooks"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            action_type = data.get('action', {}).get('type')
            log(f"Webhook received: {action_type}")
            
            # Загружаем состояние
            state = load_state()
            
            # Обрабатываем событие
            if action_type in ['createCard', 'updateCard', 'deleteCard']:
                card_data = data['action']['data'].get('card', {})
                card_id = card_data.get('id')
                card_name = card_data.get('name', '')
                
                change_msg = None
                
                if action_type == 'createCard':
                    list_name = data['action']['data'].get('list', {}).get('name', 'Unknown')
                    change_msg = f"➕ Создана: {card_name}\n   Колонка: {list_name}"
                    state['cards'][card_id] = {'name': card_name, 'list': list_name}
                
                elif action_type == 'updateCard':
                    old_list = data['action']['data'].get('listBefore', {}).get('name')
                    new_list = data['action']['data'].get('listAfter', {}).get('name')
                    
                    if old_list and new_list and old_list != new_list:
                        change_msg = f"➡️ {card_name}\n   {old_list} → {new_list}"
                        if card_id in state['cards']:
                            state['cards'][card_id]['list'] = new_list
                    elif 'name' in data['action']['data'].get('old', {}):
                        old_name = data['action']['data']['old']['name']
                        change_msg = f"✏️ Переименована:\n   {old_name} → {card_name}"
                        if card_id in state['cards']:
                            state['cards'][card_id]['name'] = card_name
                
                elif action_type == 'deleteCard':
                    change_msg = f"🗑️ Удалена: {card_name}"
                    if card_id in state['cards']:
                        del state['cards'][card_id]
                
                # Сохраняем изменение
                if change_msg:
                    log(change_msg)
                    state['changes'].append({
                        'timestamp': datetime.now().isoformat(),
                        'type': action_type,
                        'message': change_msg,
                        'critical': is_critical_card(card_name)
                    })
                    
                    # Уведомляем только если критическая задача
                    if is_critical_card(card_name):
                        notify_telegram(f"🔴 Mission Control:\n{change_msg}")
            
            # Сохраняем состояние
            save_state(state)
            
            # Отправляем ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            
        except Exception as e:
            log(f"ERROR: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_GET(self):
        """Health check"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    log(f"Webhook server running on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
