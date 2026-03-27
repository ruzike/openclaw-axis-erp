#!/usr/bin/env python3
import json
import logging
import os
import requests
import datetime
import urllib.parse
from datetime import timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Конфигурация API Gateway OpenClaw
OPENCLAW_URL = "http://localhost:18789"
GATEWAY_URL = "http://localhost:3000" # fallback для некоторых эндпоинтов

# Какие агенты сканировать
TARGET_AGENTS = ["main", "ops", "sales", "hr", "devops", "tech", "qc", "finance"]

# Настройка модели
AUDIT_MODEL = "anthropic/claude-sonnet-4-6" # или 4-5 в зависимости от доступности

def get_auth_headers():
    token_path = os.path.expanduser("~/.openclaw/gateway.token")
    if os.path.exists(token_path):
         with open(token_path, "r") as f:
             token = f.read().strip()
             return {"Authorization": f"Bearer {token}"}
    return {}

def fetch_sessions():
    logging.info("♻️ Загрузка списка сессий...")
    try:
        response = requests.get(f"{OPENCLAW_URL}/api/sessions", headers=get_auth_headers(), params={"limit": 50})
        response.raise_for_status()
        return response.json().get('sessions', [])
    except Exception as e:
        logging.error(f"Ошибка загрузки сессий: {e}")
        return []

def fetch_history(session_key):
    logging.info(f"♻️ Загрузка истории для сессии: {session_key}")
    try:
        req_params = urllib.parse.urlencode({"sessionKey": session_key, "limit": 20})
        # endpoint history обычно тут
        response = requests.get(f"{OPENCLAW_URL}/api/sessions/history?{req_params}", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json().get('messages', [])
        else:
            logging.error(f"Не удалось выгрузить {session_key}: {response.status_code} {response.text}")
            return []
    except Exception as e:
        logging.error(f"Ошибка выгрузки истории {session_key}: {e}")
        return []

def format_messages_for_dump(messages, agent_name):
    dump = []
    dump.append(f"\n--- НАЧАЛО ЛОГА АГЕНТА: {agent_name.upper()} ---")
    
    # Реверсируем, так как API отдает от новых к старым
    for msg in reversed(messages):
        role = msg.get('role', 'unknown')
        if role == 'system' or msg.get('type') == 'thinking':
            continue
        
        timestamp = msg.get('timestamp')
        content = msg.get('content', '')
        
        # Парсинг контента
        text_content = ""
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_content += block.get('text', '')
                elif isinstance(block, dict) and block.get('type') == 'toolCall':
                     text_content += f"[Tool Call: {block.get('name')} {block.get('arguments')}]\n"
        elif isinstance(content, str):
            text_content = content
            
        time_str = datetime.datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S') if timestamp else "unknown"
        
        # Исключаем пустые сообщения и внутренние промпты
        if not text_content.strip() or "[System Message]" in text_content[:50]:
             continue
             
        sender = "Руслан/Пользователь" if role == "user" else f"Агент {agent_name.capitalize()}"
        dump.append(f"[{time_str}] {sender}:\n{text_content}\n")
        
    dump.append(f"--- КОНЕЦ ЛОГА АГЕНТА: {agent_name.upper()} ---\n")
    return "\n".join(dump)

def run_audit(dump_text):
    logging.info(f"🧠 Запуск нейро-аудита через {AUDIT_MODEL}...")
    
    # Читаем системный промпт
    prompt_path = os.path.expanduser("~/openclaw/scripts/asb-audit/asb-auditor-prompt.md")
    with open(prompt_path, "r") as f:
        system_prompt = f.read()

    user_prompt = f"Проведи ASB-аудит (Академия Системного Бизнеса) на основе логов ниже. Выяви утечки управления, несоблюдение стандартов и хорошие практики. Сгенерируй отчет и правила внедрения.\n\nЛОГИ:\n{dump_text}"

    payload = {
        "model": AUDIT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }
    
    try:
        logging.info("Отправка запроса к Claude API...")
        response = requests.post(
            f"{OPENCLAW_URL}/v1/chat/completions",
            headers=get_auth_headers(),
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        reply = response.json()
        return reply['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"Ошибка работы нейро-аудитора: {e}")
        return "ОШИБКА ГЕНЕРАЦИИ ОТЧЕТА: Проверьте логи сети."

def main():
    logging.info("🚀 Запуск ASB Scanner & Auditor")
    sessions = fetch_sessions()
    
    full_dump = ""
    processed_agents = set()
    
    # Ищем подходящие сессии
    for s in sessions:
        key = s.get('key', '')
        if not key.startswith("agent:"):
            continue
            
        parts = key.split(':')
        if len(parts) >= 2:
            agent_id = parts[1]
            if agent_id in TARGET_AGENTS and agent_id not in processed_agents:
                logging.info(f"Найден целевой агент: {agent_id}. Извлекаем историю...")
                history = fetch_history(key)
                if history:
                    full_dump += format_messages_for_dump(history, agent_id)
                    processed_agents.add(agent_id)
                    
    if not full_dump.strip():
        logging.warning("⚠️ Логи не найдены или пусты. Завершение.")
        return

    # Запуск анализа
    report_text = run_audit(full_dump)
    
    # Сохранение
    date_str = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    report_path = os.path.expanduser(f"~/openclaw/reports/ASB-AUDIT_{date_str}.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
        
    logging.info(f"✅ ASB-Аудит завершен! Отчет сохранен в:\n{report_path}")

if __name__ == "__main__":
    main()
