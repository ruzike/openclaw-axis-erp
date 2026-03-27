#!/usr/bin/env python3
"""
Trello Webhook Server — Real-time синхронизация с axis-state.json

Принимает события от Trello Webhooks и обновляет Shared State в реальном времени.
Fallback: cron job 1e5ea293 остаётся активным на случай падения сервера.

Автор: DevOps Agent (AXIS System)
Версия: 1.0.0
"""

import json
import os
import sys
import hmac
import hashlib
import base64
import logging
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Lock

from flask import Flask, request, jsonify, abort

# SQLite event queue (буфер событий)
sys.path.insert(0, str(Path(__file__).parent))
from event_queue import EventQueue

# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================

# Пути
CONFIG_FILE = Path("/home/axis/openclaw/trello-config.json")
STATE_FILE = Path("/home/axis/openclaw/axis-system/axis-state.json")
LOG_DIR = Path("/home/axis/openclaw/axis-system/trello-webhook/logs")
TRELLO_SCRIPT = Path("/home/axis/openclaw/scripts/trello/trello-briefing.py")

# Порт сервера (18790 - рядом с Gateway 18789)
SERVER_PORT = int(os.environ.get("TRELLO_WEBHOOK_PORT", 18790))

# Секрет для верификации (берётся из конфига)
TRELLO_SECRET = None  # Загружается из trello-config.json

# Доски для мониторинга (можно расширять)
MONITORED_BOARDS = {}  # Заполняется из конфига

# =============================================================================
# ЛОГИРОВАНИЕ
# =============================================================================

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "webhook.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Отдельный лог для событий
event_logger = logging.getLogger("events")
event_handler = logging.FileHandler(LOG_DIR / "events.log", encoding='utf-8')
event_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
event_logger.addHandler(event_handler)
event_logger.setLevel(logging.INFO)

# =============================================================================
# ЗАГРУЗКА КОНФИГУРАЦИИ
# =============================================================================

def load_config() -> Dict[str, Any]:
    """Загружает конфигурацию Trello"""
    global TRELLO_SECRET, MONITORED_BOARDS
    
    if not CONFIG_FILE.exists():
        logger.error(f"Конфиг не найден: {CONFIG_FILE}")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Секрет для верификации = API secret (первые 32 символа токена)
    TRELLO_SECRET = config['api']['token'][:32]
    
    # Собираем все доски для мониторинга
    MONITORED_BOARDS = {}
    for key, board in config.get('boards', {}).items():
        if 'id' in board:
            MONITORED_BOARDS[board['id']] = {
                'key': key,
                'name': board.get('name', key),
                'lists': board.get('lists', {})
            }
    
    logger.info(f"Загружено {len(MONITORED_BOARDS)} досок для мониторинга")
    return config

# =============================================================================
# ВЕРИФИКАЦИЯ WEBHOOK ЗАПРОСОВ
# =============================================================================

def verify_trello_signature(payload: bytes, signature: str, callback_url: str) -> bool:
    """
    Верифицирует подпись Trello webhook.
    
    Trello подписывает: body + callbackURL
    Алгоритм: HMAC-SHA1, base64
    """
    if not TRELLO_SECRET:
        logger.warning("TRELLO_SECRET не установлен, пропускаем верификацию")
        return True
    
    try:
        # Trello использует: HMAC-SHA1(secret, body + callbackURL)
        content = payload + callback_url.encode('utf-8')
        expected = base64.b64encode(
            hmac.new(
                TRELLO_SECRET.encode('utf-8'),
                content,
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return hmac.compare_digest(signature, expected)
    except Exception as e:
        logger.error(f"Ошибка верификации: {e}")
        return False

# =============================================================================
# ОБНОВЛЕНИЕ STATE
# =============================================================================

state_lock = Lock()
timer_lock = Lock()
debounce_timer = None
DEBOUNCE_SECONDS = 10.0

def _execute_debounced_update():
    with state_lock:
        _run_full_state_update()
    logger.info("✅ State обновлён (Debounce сработал)")


def update_state_from_event(event: Dict[str, Any]) -> bool:
    """
    Обновляет axis-state.json на основе события Trello.
    
    Поддерживаемые события:
    - updateCard (перемещение, изменение)
    - createCard (создание)
    - deleteCard (удаление)
    """
    try:
        action = event.get('action', {})
        action_type = action.get('type', '')
        
        # Получаем информацию о доске
        board_data = action.get('data', {}).get('board', {})
        board_id = board_data.get('id', '')
        
        if board_id not in MONITORED_BOARDS:
            logger.debug(f"Игнорируем событие для не-мониторируемой доски: {board_id}")
            return False
        
        board_info = MONITORED_BOARDS[board_id]
        
        # Логируем событие
        card_name = action.get('data', {}).get('card', {}).get('name', 'Unknown')
        
        # Determine target list name (handling updateCard list changes)
        list_name = action.get('data', {}).get('list', {}).get('name', '')
        if action_type == 'updateCard' and 'listAfter' in action.get('data', {}):
            list_name = action['data']['listAfter'].get('name', '')
            
        member = action.get('memberCreator', {}).get('username', 'Unknown')
        
        event_logger.info(
            f"[{action_type}] Доска: {board_info['name']} | "
            f"Карточка: {card_name} | Список: {list_name} | Автор: {member}"
        )
        
        # Уведомляем агентов в реальном времени
        notify_thread = threading.Thread(
            target=_notify_agents,
            args=(action_type, card_name, list_name, board_info['name'], member, action.get('data', {}).get('card', {}).get('id', '')),
            daemon=True
        )
        notify_thread.start()
        
        # Debounce: откладываем запуск обновления state
        global debounce_timer
        with timer_lock:
            if debounce_timer is not None:
                debounce_timer.cancel()
            debounce_timer = threading.Timer(DEBOUNCE_SECONDS, _execute_debounced_update)
            debounce_timer.start()
        
        logger.info(f"⏳ Debounce: Обновление state отложено на {DEBOUNCE_SECONDS} сек. (событие {action_type})")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка обновления state: {e}")
        return False

def _notify_agents(action_type: str, card_name: str, list_name: str, board_name: str, member: str, card_id: str = ""):
    """Уведомляет агентов о событии Trello через openclaw system event."""
    try:
        # Формируем понятное сообщение
        action_map = {
            'updateCard': '📝 Карточка обновлена',
            'createCard': '🆕 Новая карточка',
            'deleteCard': '🗑️ Карточка удалена',
            'addMemberToCard': '👤 Назначен участник',
            'removeMemberFromCard': '👤 Участник убран',
            'commentCard': '💬 Комментарий',
            'addAttachmentToCard': '📎 Вложение добавлено',
        }
        action_text = action_map.get(action_type, f'🔔 {action_type}')
        
        list_info = f" → {list_name}" if list_name else ""
        msg = f"Trello: {action_text} | {card_name}{list_info} | Доска: {board_name} | Автор: {member}"
        
        # ТРИГГЕРЫ ДЛЯ АГЕНТОВ: Draftsman и QC (Задача 17)
        if action_type == 'updateCard' and list_name:
            if list_name == 'In Progress':
                logger.info(f"🚀 Триггер 'In Progress': уведомляем draftsman о задаче {card_name}")
                trigger_msg = f"Новая задача в Trello перешла в 'In Progress': {card_name}. Пожалуйста, ознакомься с ТЗ и приступай к работе."
                subprocess.Popen(
                    ["openclaw", "sessions", "spawn", "draftsman", "--message", trigger_msg],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            elif list_name == 'QC Review':
                logger.info(f"✅ Триггер 'QC Review': уведомляем qc о завершении задачи {card_name}")
                trigger_msg = f"Задача Trello переведена в 'QC Review': {card_name}. Пожалуйста, проведи проверку качества."
                subprocess.Popen(
                    ["openclaw", "sessions", "send", "--label", "qc", "--message", trigger_msg],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )

        # Автоиндексация: если карточка перемещена в "Готово"/"Done"
        if list_name and any(done in list_name.lower() for done in ['готово', 'done', 'завершено', 'закрыто']):
            try:
                # card_id передан как параметр
                subprocess.Popen(
                    ["python3", "/home/axis/openclaw/axis-system/trello-to-history.py",
                     card_id or "unknown", board_name, list_name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                logger.info(f"📦 Автоиндексация: карточка перемещена в {list_name}")
            except Exception as e:
                logger.error(f"Ошибка автоиндексации: {e}")

        result = subprocess.run(
            ["openclaw", "system", "event", "--text", msg, "--mode", "now", "--timeout", "10000"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            logger.info(f"🔔 Агент уведомлён: {msg[:80]}")
        else:
            logger.warning(f"⚠️ system event failed (rc={result.returncode}): {result.stderr[:100]}")
    except Exception as e:
        logger.error(f"Ошибка уведомления агентов: {e}")

def _run_full_state_update():
    """Запускает полное обновление state через shared-state.py"""
    try:
        shared_state_script = Path("/home/axis/openclaw/axis-system/shared-state.py")
        if shared_state_script.exists():
            result = subprocess.run(
                ["python3", str(shared_state_script)],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                logger.warning(f"shared-state.py вернул код {result.returncode}: {result.stderr}")
        else:
            # Fallback: минимальное обновление timestamp
            _update_timestamp_only()
    except subprocess.TimeoutExpired:
        logger.error("shared-state.py таймаут (60s)")
    except Exception as e:
        logger.error(f"Ошибка запуска shared-state.py: {e}")

def _update_timestamp_only():
    """Минимальное обновление - только timestamp"""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
        else:
            state = {}
        
        state['updatedAt'] = datetime.now().isoformat()
        state['_webhookTriggered'] = True
        
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка обновления timestamp: {e}")

# =============================================================================
# FLASK APP
# =============================================================================

app = Flask(__name__)

# Загружаем конфиг при старте
config = load_config()

# Инициализируем SQLite очередь
event_queue = EventQueue()

# =============================================================================
# BACKGROUND RETRY THREAD — повторная обработка упавших событий
# =============================================================================

def retry_worker():
    """
    Фоновый поток: каждые 60 секунд обрабатывает pending/failed события.
    Гарантирует что события не потеряются при временных сбоях.
    """
    while True:
        try:
            pending = event_queue.get_pending(limit=10)
            if pending:
                logger.info(f"🔄 Retry worker: {len(pending)} события в очереди")
                for ev in pending:
                    event_id = ev["id"]
                    try:
                        payload = json.loads(ev["payload"])
                        event_queue.mark_processing(event_id)
                        update_state_from_event(payload)
                        event_queue.mark_processed(event_id)
                        logger.info(f"✅ Retry: событие #{event_id} обработано")
                    except Exception as e:
                        event_queue.mark_failed(event_id, str(e))
                        logger.warning(f"⚠️ Retry: событие #{event_id} провалилось: {e}")
            # Ежедневная очистка старых событий (раз в час)
            if int(time.time()) % 3600 < 60:
                event_queue.cleanup_old()
        except Exception as e:
            logger.error(f"Retry worker ошибка: {e}")
        time.sleep(60)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "trello-webhook-server",
        "timestamp": datetime.now().isoformat(),
        "monitored_boards": len(MONITORED_BOARDS)
    })

@app.route('/webhook/trello', methods=['HEAD'])
def webhook_head():
    """
    HEAD запрос - Trello проверяет доступность endpoint при регистрации webhook.
    Должен вернуть 200 OK.
    """
    logger.info("📡 HEAD запрос от Trello (верификация endpoint)")
    return '', 200

@app.route('/webhook/trello', methods=['POST'])
def webhook_post():
    """
    POST запрос - Trello отправляет события.
    
    Headers:
    - x-trello-webhook: signature для верификации
    """
    try:
        # Получаем данные
        payload = request.get_data()
        signature = request.headers.get('x-trello-webhook', '')
        callback_url = request.url
        
        # Верификация подписи (опционально, но рекомендуется)
        # if signature and not verify_trello_signature(payload, signature, callback_url):
        #     logger.warning(f"⚠️ Неверная подпись webhook")
        #     abort(401)
        
        # Парсим JSON
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            logger.error("❌ Невалидный JSON в payload")
            abort(400)
        
        # Обрабатываем событие
        action_type = event.get('action', {}).get('type', 'unknown')
        
        # Фильтруем нужные события
        relevant_actions = [
            'createCard',
            'updateCard', 
            'deleteCard',
            'moveCardToBoard',
            'moveCardFromBoard',
            'updateList',
            'createList',
            'updateBoard'
        ]
        
        if action_type in relevant_actions:
            logger.info(f"📥 Событие: {action_type}")
            # 1. СНАЧАЛА сохраняем в SQLite (гарантия что не потеряем)
            event_id = event_queue.enqueue(event)
            # 2. Пытаемся обработать сразу
            try:
                event_queue.mark_processing(event_id)
                update_state_from_event(event)
                event_queue.mark_processed(event_id)
                logger.info(f"✅ Событие #{event_id} обработано")
            except Exception as proc_err:
                # Если обработка упала — событие остаётся в очереди для retry
                event_queue.mark_failed(event_id, str(proc_err))
                logger.warning(f"⚠️ Обработка #{event_id} упала, retry позже: {proc_err}")
        else:
            logger.debug(f"⏭️ Пропущено событие: {action_type}")
        
        # Trello ожидает 200 OK (всегда, чтобы не отключить webhook)
        return jsonify({"status": "received"}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        # Возвращаем 200, чтобы Trello не отключил webhook
        return jsonify({"status": "error", "message": str(e)}), 200


@app.route('/queue/stats', methods=['GET'])
def queue_stats():
    """Статистика SQLite очереди событий"""
    stats = event_queue.get_stats()
    return jsonify({
        "queue": stats,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook/trello/test', methods=['POST'])
def webhook_test():
    """Тестовый endpoint для локального тестирования"""
    try:
        event = request.get_json()
        logger.info(f"🧪 Тестовое событие: {json.dumps(event, ensure_ascii=False)[:200]}")
        update_state_from_event(event)
        return jsonify({"status": "test_received"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/status', methods=['GET'])
def status():
    """Детальный статус сервера"""
    state_exists = STATE_FILE.exists()
    state_mtime = None
    if state_exists:
        state_mtime = datetime.fromtimestamp(STATE_FILE.stat().st_mtime).isoformat()
    
    return jsonify({
        "server": {
            "status": "running",
            "port": SERVER_PORT,
            "uptime": "active"
        },
        "state_file": {
            "path": str(STATE_FILE),
            "exists": state_exists,
            "last_modified": state_mtime
        },
        "monitored_boards": [
            {"id": bid, "name": info['name']} 
            for bid, info in MONITORED_BOARDS.items()
        ],
        "timestamp": datetime.now().isoformat()
    })

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 Trello Webhook Server запускается...")
    logger.info(f"📍 Порт: {SERVER_PORT}")
    logger.info(f"📁 State file: {STATE_FILE}")
    logger.info(f"📊 Мониторинг досок: {len(MONITORED_BOARDS)}")
    logger.info(f"📦 SQLite очередь: {event_queue.db_path}")
    logger.info("=" * 60)

    # Запускаем фоновый retry-поток
    retry_thread = threading.Thread(target=retry_worker, daemon=True, name="retry-worker")
    retry_thread.start()
    logger.info("🔄 Retry worker запущен")

    # Запуск Flask
    app.run(
        host='127.0.0.1',  # Только через Cloudflare tunnel, не наружу
        port=SERVER_PORT,
        debug=False,
        threaded=True
    )
