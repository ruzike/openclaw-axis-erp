#!/usr/bin/env python3
"""
model-router.py - Роутер выбора модели для задач

Анализирует тип задачи и возвращает оптимальную модель.
Используется в cron-задачах и автоматизациях для экономии токенов.
"""

import sys
import json
import os

# Дефолтные значения (если не заданы через ENV)
DEFAULT_MODELS = {
    "haiku": "google/gemini-3-flash-preview",  # Быстрая/дешевая замена Haiku
    "sonnet": "google/gemini-3.1-pro-preview", # Мощная замена Sonnet/Opus
    "gemini": "google/gemini-3-pro-preview",
}

def get_model_alias(alias_key):
    """Получает полный ID модели из ENV или дефолта"""
    env_key = f"MODEL_ALIAS_{alias_key.upper()}"
    return os.environ.get(env_key, DEFAULT_MODELS.get(alias_key, "google/gemini-3.1-pro-preview"))

# Маппинг типов задач на категории моделей
TASK_CATEGORIES = {
    # "haiku" = Быстрые, простые, шаблонные задачи
    "haiku": [
        "trello_status_check",       # Проверка статусов Trello без анализа
        "deadline_simple_check",     # Простая проверка дедлайнов
        "ping_template",             # Шаблонные напоминания по расписанию
        "data_fetch",                # Сбор данных (без анализа)
        "simple_format",             # Форматирование списков/данных
        "heartbeat_check",           # Простые heartbeat проверки
    ],
    
    # "sonnet" = Сложный анализ, стратегия, общение с Русланом
    "sonnet": [
        "user_chat",                 # Любое общение с Русланом
        "strategy_analysis",         # Стратегический анализ
        "priority_decision",         # Решения по приоритизации
        "escalation_decision",       # Решение об эскалации
        "complex_report",            # Сложные отчёты с анализом
        "team_communication",        # Персонализированные сообщения команде
        "planning",                  # Планирование (недельное, проектное)
        "retrospective",             # Ретроспективы
    ],
    
    # "gemini" = Агент team (специфичные задачи)
    "gemini": [
        "team_agent_default",        # Всё что идёт через агент team
    ]
}

def classify_task_category(task_description: str) -> str:
    """
    Классифицирует задачу на категорию ('haiku', 'sonnet', 'gemini') на основе описания.
    """
    if not task_description:
        return "sonnet"
        
    desc_lower = task_description.lower()
    
    # Sonnet - высокий приоритет (стратегия, решения)
    if any(kw in desc_lower for kw in ["руслан", "стратегия", "приоритет", "эскалация", "решение", "планирование", "анализ"]):
        return "sonnet"
    
    # Haiku - шаблонные действия (проверки, пинги)
    if any(kw in desc_lower for kw in ["проверка", "статус", "шаблон", "напоминание", "собрать", "список"]):
        return "haiku"
    
    # Default - Sonnet (безопасность превыше экономии)
    return "sonnet"

def route_task(task_type: str = None, task_description: str = None) -> dict:
    """
    Определяет модель для задачи.
    
    Args:
        task_type: явный тип задачи (ключ из TASK_CATEGORIES или значение внутри списков)
        task_description: описание задачи (для автоклассификации)
    
    Returns:
        {"category": "alias", "full_model": "provider/model", "reason": "..."}
    """
    
    category = "sonnet" # Default fallback
    reason = "Default fallback (safety first)"

    # 1. Если передан task_type
    if task_type:
        # Проверяем, является ли task_type названием категории (haiku/sonnet)
        if task_type in TASK_CATEGORIES:
            category = task_type
            reason = f"Explicit category: {task_type}"
        else:
            # Ищем, в какой категории лежит этот task_type
            found = False
            for cat, tasks in TASK_CATEGORIES.items():
                if task_type in tasks:
                    category = cat
                    reason = f"Explicit task type found in {cat}: {task_type}"
                    found = True
                    break
            if not found:
                 reason = f"Task type '{task_type}' not found, defaulting to sonnet"

    # 2. Если task_type нет, но есть description -> автоклассификация
    elif task_description:
        category = classify_task_category(task_description)
        reason = f"Classified from description: {task_description[:50]}..."
    
    # Получаем реальное имя модели для этой категории
    full_model = get_model_alias(category)

    return {
        "category": category,
        "full_model": full_model,
        "reason": reason
    }


def main():
    """CLI интерфейс"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Model router - выбор оптимальной модели для задачи")
    parser.add_argument("--task-type", help="Явный тип задачи или категория (haiku, sonnet...)")
    parser.add_argument("--description", help="Описание задачи (для автоклассификации)")
    parser.add_argument("--list-types", action="store_true", help="Показать все типы задач")
    parser.add_argument("--json", action="store_true", help="Вывод в JSON")
    
    args = parser.parse_args()
    
    if args.list_types:
        print("📋 Типы задач и категории моделей:\n")
        for cat, tasks in TASK_CATEGORIES.items():
            model_id = get_model_alias(cat)
            print(f"🔹 {cat.upper()} (Mapped to: {model_id}):")
            for task in tasks:
                print(f"   - {task}")
            print()
        return
    
    if not args.task_type and not args.description:
        # Если ничего не передано, но скрипт запущен - можно вывести help
        # Но для совместимости с pipe иногда лучше вернуть default
        pass
    
    result = route_task(task_type=args.task_type, task_description=args.description)
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"✅ Category: {result['category']}")
        print(f"🤖 Model: {result['full_model']}")
        print(f"📝 Reason: {result['reason']}")


if __name__ == "__main__":
    main()
