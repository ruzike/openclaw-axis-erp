#!/usr/bin/env python3
"""
generate_office.py — генератор интерактивного AI-офиса AXIS
Читает MEMORY.md каждого агента, парсит секции, генерирует agents-status.json и office.html
"""

import os
import re
import json
import datetime
from pathlib import Path

# ========================
# КОНФИГ АГЕНТОВ
# ========================

AGENTS_BASE = "/home/axis/openclaw/agents"
DASHBOARD_DIR = "/home/axis/openclaw/dashboard"

AGENTS = [
    {
        "id": "main",
        "name": "Main",
        "role": "COO — Координация системы",
        "emoji": "🧠",
        "color": "#6366f1",
        "room": "management",
        "seat": {"x": 2, "y": 1}
    },
    {
        "id": "ops",
        "name": "Ops",
        "role": "Ритуалы и координация команды",
        "emoji": "⚙️",
        "color": "#10b981",
        "room": "management",
        "seat": {"x": 4, "y": 1}
    },
    {
        "id": "tech",
        "name": "Tech",
        "role": "Регламенты, SOP, автоматизация",
        "emoji": "🔧",
        "color": "#3b82f6",
        "room": "tech",
        "seat": {"x": 1, "y": 3}
    },
    {
        "id": "devops",
        "name": "DevOps",
        "role": "Инфраструктура и API",
        "emoji": "🖥️",
        "color": "#f59e0b",
        "room": "tech",
        "seat": {"x": 3, "y": 3}
    },
    {
        "id": "sales",
        "name": "Sales",
        "role": "Лиды, продажи, договоры",
        "emoji": "💼",
        "color": "#ec4899",
        "room": "sales",
        "seat": {"x": 1, "y": 5}
    },
    {
        "id": "finance",
        "name": "Finance",
        "role": "Сметы, счета, финансы",
        "emoji": "💰",
        "color": "#84cc16",
        "room": "sales",
        "seat": {"x": 3, "y": 5}
    },
    {
        "id": "shket",
        "name": "Шкет",
        "role": "SMM, Telegram-канал",
        "emoji": "📣",
        "color": "#a855f7",
        "room": "creative",
        "seat": {"x": 5, "y": 3}
    },
    {
        "id": "hr",
        "name": "HR",
        "role": "Найм, адаптация, KPI",
        "emoji": "👥",
        "color": "#06b6d4",
        "room": "management",
        "seat": {"x": 6, "y": 1}
    },
    {
        "id": "qc",
        "name": "QC",
        "role": "Контроль качества, ОКК",
        "emoji": "🔍",
        "color": "#f97316",
        "room": "tech",
        "seat": {"x": 5, "y": 1}
    },
    {
        "id": "draftsman",
        "name": "Чертёжник",
        "role": "Чертежи AutoCAD/Revit",
        "emoji": "📐",
        "color": "#14b8a6",
        "room": "production",
        "seat": {"x": 1, "y": 7}
    },
    {
        "id": "team",
        "name": "Team",
        "role": "Помощник Мираса и Бахытжана",
        "emoji": "🤝",
        "color": "#64748b",
        "room": "production",
        "seat": {"x": 3, "y": 7}
    },
    {
        "id": "strategy",
        "name": "Strategy",
        "role": "Стратегия, KPI, рынок",
        "emoji": "🎯",
        "color": "#e11d48",
        "room": "management",
        "seat": {"x": 8, "y": 1}
    },
]

# ========================
# ПАРСИНГ MEMORY.md
# ========================

def parse_memory(agent_id):
    memory_path = Path(AGENTS_BASE) / agent_id / "MEMORY.md"
    soul_path = Path(AGENTS_BASE) / agent_id / "SOUL.md"

    result = {
        "last_update": None,
        "last_update_raw": None,
        "tasks": [],
        "questions": [],
        "soul_size": 0,
        "status": "red",
        "active": False
    }

    # Размер SOUL.md
    if soul_path.exists():
        result["soul_size"] = soul_path.stat().st_size

    if not memory_path.exists():
        return result

    # Дата последнего изменения файла
    mtime = memory_path.stat().st_mtime
    file_mtime = datetime.datetime.fromtimestamp(mtime)
    result["last_update"] = file_mtime.strftime("%Y-%m-%d %H:%M")
    result["last_update_raw"] = mtime

    # Статус по дате
    now = datetime.datetime.now()
    age_hours = (now - file_mtime).total_seconds() / 3600
    if age_hours < 24:
        result["status"] = "green"
        result["active"] = True
    elif age_hours < 48:
        result["status"] = "yellow"
    else:
        result["status"] = "red"

    # Парсинг содержимого
    content = memory_path.read_text(encoding="utf-8")

    # Извлечение даты обновления из текста
    date_match = re.search(r'(?:Последнее обновление|Last updated|Дата)[:\s]+([^\n]+)', content)
    if date_match:
        result["last_update_text"] = date_match.group(1).strip()

    # Секция "Текущие задачи"
    tasks_section = re.search(
        r'##\s*(?:📌\s*)?(?:Текущие задачи|Current Tasks|Задачи)[^\n]*\n(.*?)(?=\n##|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    if tasks_section:
        tasks_text = tasks_section.group(1)
        tasks = []
        for line in tasks_text.split('\n'):
            line = line.strip()
            # Ищем строки с чекбоксами или маркерами
            if re.match(r'^[-*]\s*\[.?\]', line) or re.match(r'^[-*•]\s+\*?\*?', line):
                # Убираем markdown разметку чекбоксов
                clean = re.sub(r'^[-*•]\s*\[.?\]\s*', '', line)
                clean = re.sub(r'^[-*•]\s*\*?\*?', '', clean)
                clean = clean.strip('*').strip()
                if clean and len(clean) > 3:
                    tasks.append(clean)
        result["tasks"] = tasks[:5]  # Максимум 5 задач

    # Секция "Открытые вопросы к Руслану"
    questions_section = re.search(
        r'##\s*(?:❓\s*|🚨\s*)?Открытые вопросы к Руслану[^\n]*\n(.*?)(?=\n##|\Z)',
        content, re.DOTALL
    )
    if questions_section:
        q_text = questions_section.group(1)
        questions = []
        for line in q_text.split('\n'):
            line = line.strip()
            # Строки таблицы markdown
            if line.startswith('|') and not line.startswith('|---') and not line.startswith('| ---'):
                cols = [c.strip() for c in line.split('|') if c.strip()]
                if cols and len(cols[0]) > 5 and not cols[0].lower().startswith('вопрос'):
                    questions.append(cols[0][:120])
            # Обычные строки с маркерами
            elif re.match(r'^[-*•⏳]\s+', line):
                clean = re.sub(r'^[-*•⏳]\s*', '', line).strip()
                if clean and len(clean) > 5 and 'нет открытых' not in clean.lower():
                    questions.append(clean[:120])
            # Строки "Нет открытых вопросов"
            elif 'нет открытых' in line.lower():
                pass  # пропускаем
        result["questions"] = questions[:4]

    return result


# ========================
# ГЕНЕРАЦИЯ JSON
# ========================

def generate_json():
    data = {
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agents": []
    }

    for agent_cfg in AGENTS:
        memory = parse_memory(agent_cfg["id"])
        agent_data = {**agent_cfg, **memory}
        data["agents"].append(agent_data)

    json_path = Path(DASHBOARD_DIR) / "agents-status.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Сохранён: {json_path}")
    return data


# ========================
# ГЕНЕРАЦИЯ HTML
# ========================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="300">
<title>🏢 AI Офис AXIS</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    background: #0d0d1a;
    font-family: 'Inter', system-ui, sans-serif;
    overflow-x: hidden;
    min-height: 100vh;
    color: #e0e0e0;
}

/* ===== HEADER ===== */
.header {
    text-align: center;
    padding: 16px 20px;
    background: linear-gradient(180deg, #0a0a1a 0%, #0d0d1a 100%);
    border-bottom: 3px solid #1e1e4a;
    position: relative;
}
.header h1 { font-size: 14px; color: #6366f1; text-shadow: 0 0 10px #6366f199; margin-bottom: 6px; }
.header .subtitle { font-size: 13px; color: #666; }
.header .timestamp { font-size: 13px; color: #444; margin-top: 4px; }
.refresh-btn {
    position: absolute; right: 16px; top: 50%; transform: translateY(-50%);
    background: #1e1e4a; border: 2px solid #6366f1; color: #6366f1;
    font-family: 'Inter', system-ui, sans-serif; font-size: 13px;
    padding: 6px 10px; cursor: pointer; transition: all 0.2s;
}
.refresh-btn:hover { background: #6366f1; color: #fff; }

/* ===== OFFICE FLOOR PLAN ===== */
.office-wrapper {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.floor-plan {
    display: grid;
    grid-template-rows: auto auto auto auto;
    gap: 12px;
    width: 100%;
}

/* ===== ROOMS ===== */
.room {
    border: 3px solid;
    border-radius: 4px;
    padding: 12px;
    position: relative;
    background: rgba(255,255,255,0.02);
}
.room-label {
    position: absolute;
    top: -10px; left: 12px;
    font-size: 13px;
    padding: 2px 8px;
    background: #0d0d1a;
    border: 2px solid currentColor;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.room-ruslan {
    border-color: #ffd700;
    background: rgba(255, 215, 0, 0.04);
    grid-row: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    min-height: 100px;
}
.room-ruslan .room-label { color: #ffd700; }

.room-management {
    border-color: #6366f1;
    grid-row: 2;
}
.room-management .room-label { color: #6366f1; }

.room-tech {
    border-color: #3b82f6;
    grid-row: 3;
}
.room-tech .room-label { color: #3b82f6; }

.room-salesrow {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    grid-row: 4;
}

.room-sales-inner {
    border: 3px solid #ec4899;
    border-radius: 4px;
    padding: 12px;
    position: relative;
    background: rgba(255,255,255,0.02);
}
.room-sales-inner .room-label { color: #ec4899; }

.room-creative-inner {
    border: 3px solid #a855f7;
    border-radius: 4px;
    padding: 12px;
    position: relative;
    background: rgba(255,255,255,0.02);
}
.room-creative-inner .room-label { color: #a855f7; }

.room-production {
    border-color: #14b8a6;
    grid-row: 5;
}
.room-production .room-label { color: #14b8a6; }

/* ===== AGENTS GRID ===== */
.agents-row {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    padding-top: 8px;
    justify-content: flex-start;
    align-items: center;
}

/* ===== RUSLAN CARD ===== */
.ruslan-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    cursor: default;
}
.ruslan-sprite {
    width: 80px; height: 80px;
    background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
    border: 4px solid #ffd700;
    border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
    font-size: 32px;
    box-shadow: 0 0 20px #ffd70066, 0 0 40px #ffd70033;
    image-rendering: pixelated;
}
.ruslan-name {
    font-size: 14px;
    color: #ffd700;
    text-shadow: 0 0 8px #ffd70099;
}
.ruslan-role { font-size: 12px; color: #aa8800; }

/* ===== AGENT CARD ===== */
.agent-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    transition: transform 0.15s;
    padding: 8px;
    border-radius: 4px;
    min-width: 90px;
    position: relative;
}
.agent-card:hover { transform: scale(1.1); }
.agent-card:hover .agent-sprite { box-shadow: 0 0 20px var(--agent-color), 0 0 40px var(--agent-color-dim); }

.agent-sprite {
    width: 60px; height: 60px;
    border: 3px solid var(--agent-color);
    border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    background: var(--agent-bg);
    transition: box-shadow 0.2s;
    image-rendering: pixelated;
    position: relative;
    overflow: visible;
}

/* Пиксельный стол под агентом */
.desk {
    width: 70px; height: 14px;
    background: repeating-linear-gradient(
        90deg,
        #3a2a1a 0px, #3a2a1a 8px,
        #4a3a2a 8px, #4a3a2a 10px
    );
    border: 2px solid #5a4a3a;
    border-radius: 2px;
    margin-top: -2px;
}

.agent-name {
    font-size: 12px;
    color: var(--agent-color);
    text-align: center;
    max-width: 90px;
    line-height: 1.4;
}
.agent-role {
    font-size: 12px;
    color: #555;
    text-align: center;
    max-width: 90px;
    line-height: 1.3;
}

/* ===== STATUS INDICATOR ===== */
.status-dot {
    position: absolute;
    top: -4px; right: -4px;
    width: 12px; height: 12px;
    border-radius: 2px;
    border: 2px solid #0d0d1a;
    z-index: 2;
}
.status-green { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.status-yellow { background: #eab308; box-shadow: 0 0 6px #eab308; }
.status-red { background: #ef4444; box-shadow: 0 0 4px #ef4444; }

.pulse {
    animation: pixel-pulse 1.5s infinite;
}
@keyframes pixel-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.85); }
}

/* ===== PRODUCTION ZONE LABELS ===== */
.production-workers {
    display: flex;
    gap: 20px;
    margin-top: 8px;
    padding: 8px;
    background: rgba(20, 184, 166, 0.05);
    border: 2px dashed #14b8a633;
    border-radius: 4px;
}
.worker-badge {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
}
.worker-avatar {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #14b8a6, #0d9488);
    border: 2px solid #14b8a6;
    border-radius: 3px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
}
.worker-name { font-size: 12px; color: #14b8a6; }

/* ===== MODAL ===== */
.modal-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.85);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    padding: 16px;
}
.modal-overlay.active { display: flex; }

.modal {
    background: #0d0d1a;
    border: 3px solid var(--modal-color, #6366f1);
    border-radius: 4px;
    max-width: 560px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 0 40px var(--modal-color-dim, #6366f144);
    animation: modal-in 0.15s ease-out;
}
@keyframes modal-in {
    from { transform: scale(0.9); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

.modal-header {
    padding: 16px 20px;
    border-bottom: 2px solid var(--modal-color, #6366f1);
    display: flex;
    align-items: center;
    gap: 12px;
    position: sticky; top: 0;
    background: #0d0d1a;
    z-index: 1;
}
.modal-emoji { font-size: 28px; }
.modal-title { flex: 1; }
.modal-title h2 { font-size: 11px; color: var(--modal-color, #6366f1); margin-bottom: 4px; }
.modal-title p { font-size: 13px; color: #777; }
.modal-close {
    background: none; border: 2px solid #333; color: #666;
    font-family: 'Inter', system-ui, sans-serif; font-size: 14px;
    width: 28px; height: 28px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.15s;
}
.modal-close:hover { border-color: var(--modal-color, #6366f1); color: var(--modal-color, #6366f1); }

.modal-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 14px; }

.modal-section {}
.modal-section-title {
    font-size: 13px;
    color: #555;
    margin-bottom: 8px;
    padding-bottom: 4px;
    border-bottom: 1px solid #1e1e3a;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border: 2px solid;
    border-radius: 3px;
    font-size: 13px;
}
.status-badge.green { border-color: #22c55e; color: #22c55e; }
.status-badge.yellow { border-color: #eab308; color: #eab308; }
.status-badge.red { border-color: #ef4444; color: #ef4444; }

.task-list { list-style: none; display: flex; flex-direction: column; gap: 5px; }
.task-item {
    font-size: 12px;
    color: #aaa;
    padding: 5px 8px;
    background: #111122;
    border-left: 3px solid var(--modal-color, #6366f1);
    line-height: 1.6;
    word-break: break-word;
}

.question-list { list-style: none; display: flex; flex-direction: column; gap: 5px; }
.question-item {
    font-size: 12px;
    color: #fbbf24;
    padding: 5px 8px;
    background: #1a1500;
    border-left: 3px solid #f59e0b;
    line-height: 1.6;
    word-break: break-word;
}

.meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.meta-item {
    background: #111122;
    padding: 8px;
    border: 1px solid #1e1e3a;
    border-radius: 3px;
}
.meta-label { font-size: 12px; color: #444; margin-bottom: 4px; }
.meta-value { font-size: 13px; color: #aaa; word-break: break-word; }

.no-data { font-size: 12px; color: #333; font-style: italic; }

/* ===== LEGEND ===== */
.legend {
    display: flex;
    justify-content: center;
    gap: 20px;
    padding: 12px;
    font-size: 13px;
    color: #444;
    border-top: 2px solid #1e1e3a;
    margin-top: 20px;
}
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-dot {
    width: 10px; height: 10px;
    border-radius: 2px;
    border: 2px solid #0d0d1a;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d0d1a; }
::-webkit-scrollbar-thumb { background: #1e1e4a; }
::-webkit-scrollbar-thumb:hover { background: #6366f1; }

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
    .header h1 { font-size: 10px; }
    .floor-plan { gap: 8px; }
    .agents-row { gap: 8px; }
    .agent-card { min-width: 70px; padding: 4px; }
    .agent-sprite { width: 48px; height: 48px; font-size: 18px; }
    .desk { width: 56px; }
    .room-salesrow { grid-template-columns: 1fr; }
    .refresh-btn { display: none; }
}
</style>
</head>
<body>

<div class="header">
    <h1>🏢 AI ОФИС AXIS</h1>
    <div class="subtitle">ИНТЕРАКТИВНАЯ ВИЗУАЛИЗАЦИЯ СИСТЕМЫ</div>
    <div class="timestamp" id="ts"></div>
    <button class="refresh-btn" onclick="location.reload()">↺ ОБНОВИТЬ</button>
</div>

<div class="office-wrapper">
<div class="floor-plan">

    <!-- КАБИНЕТ РУСЛАНА + КОМАНДА -->
    <div class="room room-ruslan">
        <span class="room-label" style="color:#ffd700">👥 Команда AXIS</span>
        <div style="display: flex; justify-content: center; align-items: flex-start; gap: 40px; flex-wrap: wrap; padding: 15px 0;">
            <div class="agent-card" style="--agent-color: #ffd700; --agent-color-dim: #ffd70033; cursor: pointer;" onclick="openTeamModal('miras')" style="cursor:pointer">
                <div class="agent-sprite" style="background: #ffd70011; pointer-events:none;">👤</div>
                <div class="desk" style="pointer-events:none;"></div>
                <div class="agent-name" style="pointer-events:none;">МИРАС</div>
                <div class="agent-role" style="pointer-events:none;">Архитектор</div>
            </div>
            <div class="agent-card" style="--agent-color: #ffd700; --agent-color-dim: #ffd70033; cursor: pointer;" onclick="openTeamModal('ruslan')" style="cursor:pointer">
                <div class="agent-sprite" style="background: #ffd70011; pointer-events:none;">👤</div>
                <div class="desk" style="pointer-events:none;"></div>
                <div class="agent-name" style="pointer-events:none;">РУСЛАН</div>
                <div class="agent-role" style="pointer-events:none;">Собственник</div>
            </div>
            <div class="agent-card" style="--agent-color: #ffd700; --agent-color-dim: #ffd70033; cursor: pointer;" onclick="openTeamModal('bahytzhan')" style="cursor:pointer">
                <div class="agent-sprite" style="background: #ffd70011; pointer-events:none;">👤</div>
                <div class="desk" style="pointer-events:none;"></div>
                <div class="agent-name" style="pointer-events:none;">БАХЫТЖАН</div>
                <div class="agent-role" style="pointer-events:none;">Архитектор</div>
            </div>
        </div>
    </div>

    <!-- ЗАЛ УПРАВЛЕНИЯ -->
    <div class="room room-management">
        <span class="room-label">🧭 Зал управления</span>
        <div class="agents-row" id="room-management"></div>
    </div>

    <!-- ТЕХНИЧЕСКИЙ ОТДЕЛ -->
    <div class="room room-tech">
        <span class="room-label">⚡ Технический отдел</span>
        <div class="agents-row" id="room-tech"></div>
    </div>

    <!-- ПРОДАЖИ + КРЕАТИВ -->
    <div class="room-salesrow">
        <div class="room-sales-inner">
            <span class="room-label">💼 Продажи & Финансы</span>
            <div class="agents-row" id="room-sales"></div>
        </div>
        <div class="room-creative-inner">
            <span class="room-label">🎨 Контент & Медиа</span>
            <div class="agents-row" id="room-creative"></div>
        </div>
    </div>

    <!-- PRODUCTION ZONE -->
    <div class="room room-production">
        <span class="room-label">🏗️ Production Zone</span>
        <div class="agents-row" id="room-production"></div>
    </div>

</div><!-- /floor-plan -->
</div><!-- /office-wrapper -->

<div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#22c55e"></div> 🟢 Активен (&lt;24ч)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#eab308"></div> 🟡 Давно (&lt;48ч)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div> 🔴 Неактивен (&gt;48ч)</div>
</div>

<!-- MODAL -->
<div class="modal-overlay" id="modal" onclick="closeModal(event)">
    <div class="modal" id="modal-content">
        <div class="modal-header">
            <div class="modal-emoji" id="m-emoji"></div>
            <div class="modal-title">
                <h2 id="m-name"></h2>
                <p id="m-role"></p>
            </div>
            <button class="modal-close" onclick="closeModalDirect()">✕</button>
        </div>
        <div class="modal-body">
            <div class="modal-section">
                <div class="modal-section-title">Статус</div>
                <div id="m-status"></div>
            </div>
            <div class="modal-section">
                <div class="modal-section-title">Текущие задачи</div>
                <ul class="task-list" id="m-tasks"></ul>
            </div>
            <div class="modal-section" id="m-questions-section">
                <div class="modal-section-title">⚠️ Открытые вопросы к Руслану</div>
                <ul class="question-list" id="m-questions"></ul>
            </div>
            <div class="modal-section">
                <div class="modal-section-title">Метаданные</div>
                <div class="meta-grid">
                    <div class="meta-item">
                        <div class="meta-label">Последнее обновление MEMORY</div>
                        <div class="meta-value" id="m-update"></div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Размер SOUL.md</div>
                        <div class="meta-value" id="m-soul"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// ===== ДАННЫЕ АГЕНТОВ =====
const AGENTS_DATA = __AGENTS_DATA__;

// ===== РАСПРЕДЕЛЕНИЕ ПО КОМНАТАМ =====
const ROOM_MAP = {
    management: ["main", "ops", "hr", "strategy"],
    tech: ["tech", "devops", "qc"],
    sales: ["sales", "finance"],
    creative: ["shket"],
    production: ["draftsman", "team"]
};

function getAgentData(id) {
    return AGENTS_DATA.find(a => a.id === id);
}

// ===== СОЗДАНИЕ КАРТОЧКИ =====
function createAgentCard(agentId) {
    const a = getAgentData(agentId);
    if (!a) return null;

    const card = document.createElement("div");
    card.className = "agent-card";
    card.style.setProperty("--agent-color", a.color);
    card.style.setProperty("--agent-color-dim", a.color + "33");
    card.setAttribute("data-id", a.id);
    card.onclick = () => openModal(a.id);

    const statusClass = a.status === "green" ? "status-green" :
                        a.status === "yellow" ? "status-yellow" : "status-red";
    const pulseClass = a.status === "green" ? "pulse" : "";

    card.innerHTML = `
        <div class="agent-sprite" style="background: ${a.color}11;">
            <span class="status-dot ${statusClass} ${pulseClass}"></span>
            ${a.emoji}
        </div>
        <div class="desk"></div>
        <div class="agent-name">${a.name}</div>
        <div class="agent-role">${a.role.substring(0,30)}${a.role.length>30?"...":""}</div>
    `;
    return card;
}

// ===== РЕНДЕР ОФИСА =====
function renderOffice() {
    for (const [room, agentIds] of Object.entries(ROOM_MAP)) {
        const container = document.getElementById("room-" + room);
        if (!container) continue;
        agentIds.forEach(id => {
            const card = createAgentCard(id);
            if (card) container.appendChild(card);
        });
    }
}

// ===== МОДАЛЬНОЕ ОКНО =====
function openModal(agentId) {
    const a = getAgentData(agentId);
    if (!a) return;

    const modal = document.getElementById("modal-content");
    modal.style.setProperty("--modal-color", a.color);
    modal.style.setProperty("--modal-color-dim", a.color + "33");

    document.getElementById("m-emoji").textContent = a.emoji;
    document.getElementById("m-name").textContent = a.name.toUpperCase();
    document.getElementById("m-role").textContent = a.role;

    // Статус
    const statusTexts = {
        green: ["🟢 АКТИВЕН", "Обновлялся менее 24 часов назад", "green"],
        yellow: ["🟡 ДАВНО", "Обновлялся 24–48 часов назад", "yellow"],
        red: ["🔴 НЕАКТИВЕН", "Не обновлялся более 48 часов", "red"]
    };
    const [stLabel, stDesc, stClass] = statusTexts[a.status] || statusTexts.red;
    document.getElementById("m-status").innerHTML = `
        <div class="status-badge ${stClass}">
            <span>${stLabel}</span>
            <span style="color:#666;font-size:5px;">${stDesc}</span>
        </div>
    `;

    // Задачи
    const tasksList = document.getElementById("m-tasks");
    tasksList.innerHTML = "";
    if (a.tasks && a.tasks.length > 0) {
        a.tasks.forEach(t => {
            const li = document.createElement("li");
            li.className = "task-item";
            li.textContent = t;
            tasksList.appendChild(li);
        });
    } else {
        tasksList.innerHTML = '<li class="no-data">Нет активных задач</li>';
    }

    // Вопросы
    const questionsSection = document.getElementById("m-questions-section");
    const questionsList = document.getElementById("m-questions");
    questionsList.innerHTML = "";
    if (a.questions && a.questions.length > 0) {
        questionsSection.style.display = "";
        a.questions.forEach(q => {
            const li = document.createElement("li");
            li.className = "question-item";
            li.textContent = q;
            questionsList.appendChild(li);
        });
    } else {
        questionsSection.style.display = "none";
    }

    // Мета
    document.getElementById("m-update").textContent = a.last_update || "Неизвестно";
    const soulKb = a.soul_size ? (a.soul_size / 1024).toFixed(1) + " KB" : "—";
    document.getElementById("m-soul").textContent = soulKb;

    document.getElementById("modal").classList.add("active");
    document.body.style.overflow = "hidden";
}

function closeModalDirect() {
    document.getElementById("modal").classList.remove("active");
    document.body.style.overflow = "";
}

function closeModal(e) {
    if (e.target === document.getElementById("modal")) {
        closeModalDirect();
    }
}

// ESC key
document.addEventListener("keydown", e => {
    if (e.key === "Escape") closeModalDirect();
});

// Timestamp
function updateTimestamp() {
    const el = document.getElementById("ts");
    if (el) {
        const now = new Date();
        el.textContent = "Обновлено: " + now.toLocaleString("ru-RU");
    }
}

// ===== ДАННЫЕ КОМАНДЫ =====
const TEAM_DATA = {
    "miras": {
        name: "МИРАС", role: "Архитектор", emoji: "👤", color: "#ffd700",
        telegram: "@MIKA721S (MEMBER1_TELEGRAM_ID)",
        rituals: ["📋 Утренний брифинг — до 10:00", "📌 Trello — обновлять карточки ежедневно", "📝 План-отчёт — Пн до 08:30"],
        kpi: "+10% бонус за 100% выполнение ритуалов",
        projects: ["ЖК Лондон", "Аэропорт Аркалык", "СЭД Костанай"],
        questions: ["⚠️ Не заполняет утренний брифинг", "⚠️ Не начал чат с ботом @axis_opps_bot"]
    },
    "ruslan": {
        name: "РУСЛАН", role: "Собственник · Стратег", emoji: "👤", color: "#ffd700",
        telegram: "@ruslan_khalitov (YOUR_TELEGRAM_ID)",
        rituals: ["📋 Утренний брифинг — до 10:00", "📅 Планёрка — Пн 09:00", "🔄 Ретроспектива — Пт 18:00"],
        kpi: "Стратегические решения, контроль системы",
        projects: ["CED GROUP", "Авторский надзор"],
        questions: []
    },
    "bahytzhan": {
        name: "БАХЫТЖАН", role: "Архитектор", emoji: "👤", color: "#ffd700",
        telegram: "@Sagimbayev (MEMBER2_TELEGRAM_ID)",
        rituals: ["📋 Утренний брифинг — до 10:00", "📌 Trello — обновлять карточки ежедневно", "📝 План-отчёт — Пн до 08:30"],
        kpi: "+10% бонус за 100% выполнение ритуалов",
        projects: ["ЖК Токио", "СЭД Офис", "Шоу Рум"],
        questions: ["⚠️ Не заполняет утренний брифинг", "⚠️ Просрочка Аэропорт интерьер (дедлайн 21.02)"]
    }
};

function openTeamModal(memberId) {
    const m = TEAM_DATA[memberId];
    if (!m) return;

    const modal = document.getElementById("modal-content");
    modal.style.setProperty("--modal-color", m.color);
    modal.style.setProperty("--modal-color-dim", m.color + "33");

    document.getElementById("m-emoji").textContent = m.emoji;
    document.getElementById("m-name").textContent = m.name;
    document.getElementById("m-role").textContent = m.role;

    // Статус
    document.getElementById("m-status").innerHTML = '<div class="status-badge green"><span>🟢 СОТРУДНИК</span><span style="color:#666;font-size:11px;">Telegram: ' + m.telegram + '</span></div>';

    // Текущие задачи = ритуалы + проекты
    const tasksList = document.getElementById("m-tasks");
    tasksList.innerHTML = "";
    m.rituals.forEach(r => {
        const li = document.createElement("li");
        li.className = "task-item";
        li.textContent = r;
        tasksList.appendChild(li);
    });
    m.projects.forEach(p => {
        const li = document.createElement("li");
        li.className = "task-item";
        li.textContent = "📁 Проект: " + p;
        tasksList.appendChild(li);
    });

    // Открытые вопросы
    const questionsList = document.getElementById("m-questions");
    questionsList.innerHTML = "";
    if (m.questions && m.questions.length > 0) {
        m.questions.forEach(q => {
            const li = document.createElement("li");
            li.className = "task-item";
            li.textContent = q;
            questionsList.appendChild(li);
        });
    } else {
        questionsList.innerHTML = '<li class="no-data">Нет открытых вопросов</li>';
    }

    // Метаданные
    const metaEl = document.getElementById("m-meta");
    if (metaEl) metaEl.innerHTML = '<span>KPI: ' + m.kpi + '</span><span>Telegram: ' + m.telegram + '</span>';

    document.getElementById("modal").classList.add("active");
}

// ===== ИНИЦИАЛИЗАЦИЯ =====
renderOffice();
updateTimestamp();
setInterval(updateTimestamp, 30000);
</script>
</body>
</html>'''


def generate_html(data):
    agents_list = []
    for agent in data["agents"]:
        agents_list.append({
            "id": agent["id"],
            "name": agent["name"],
            "role": agent["role"],
            "emoji": agent["emoji"],
            "color": agent["color"],
            "status": agent["status"],
            "active": agent["active"],
            "tasks": agent.get("tasks", []),
            "questions": agent.get("questions", []),
            "last_update": agent.get("last_update"),
            "soul_size": agent.get("soul_size", 0),
        })

    agents_json = json.dumps(agents_list, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__AGENTS_DATA__", agents_json)

    html_path = Path(DASHBOARD_DIR) / "office.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"✅ Сохранён: {html_path}")


# ========================
# MAIN
# ========================

if __name__ == "__main__":
    print("🏢 Генерация AI Офис AXIS...")
    print(f"   Агентов: {len(AGENTS)}")

    os.makedirs(DASHBOARD_DIR, exist_ok=True)

    data = generate_json()
    generate_html(data)

    # Сводка
    print("\n📊 Статус агентов:")
    for agent in data["agents"]:
        status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(agent["status"], "⚪")
        tasks_count = len(agent.get("tasks", []))
        questions_count = len(agent.get("questions", []))
        print(f"   {status_icon} {agent['name']:12s} | обновлён: {agent.get('last_update','?'):16s} | задач: {tasks_count} | вопросов Руслану: {questions_count}")

    print(f"\n✅ Готово! Открыть: /home/axis/openclaw/dashboard/office.html")
