#!/usr/bin/env python3
"""
Скрипт создания 'Shared State' (Общей шины данных) для агентов AXIS.
Собирает ключевые метрики из Trello и других источников в один JSON-файл.
Запускается по Cron каждый час.
"""
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime

STATE_FILE = Path("/home/axis/openclaw/axis-system/axis-state.json")
TRELLO_SCRIPT = "/home/axis/openclaw/scripts/trello/trello-briefing.py"

def generate_state():
    state = {
        "updatedAt": datetime.now().isoformat(),
        "trello": {},
        "finance": {"status": "pending_integration"},
        "hr": {"status": "pending_integration"}
    }
    
    # Пытаемся получить данные из Trello
    try:
        if os.path.exists(TRELLO_SCRIPT):
            result = subprocess.run(
                ["python3", TRELLO_SCRIPT, "status"], 
                capture_output=True, text=True, timeout=30
            )
            # Если скрипт возвращает JSON, парсим его
            if result.stdout.strip().startswith('{'):
                state["trello"] = json.loads(result.stdout)
            else:
                state["trello"] = {"raw": result.stdout.strip()}
    except Exception as e:
        state["trello"]["error"] = str(e)

    # Сохраняем стейт
    os.makedirs(STATE_FILE.parent, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Shared State обновлен: {STATE_FILE}")

if __name__ == "__main__":
    generate_state()
