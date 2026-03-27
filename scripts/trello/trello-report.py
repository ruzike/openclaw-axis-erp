#!/usr/bin/env python3
"""Генерация отчётов по Trello (Производство C1/C2 + C3 + Стратегия)"""
import json
import requests
import sys

CONFIG_PATH = '/home/axis/openclaw/trello-config.json'
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

def get_cards(board_name, list_name):
    """Получить карточки из колонки"""
    if board_name not in config['boards']:
        return []
    board = config['boards'][board_name]
    
    if list_name not in board['lists']:
        return []
        
    list_id = board['lists'][list_name]['id']
    
    url = f"https://api.trello.com/1/lists/{list_id}/cards"
    params = {'key': API_KEY, 'token': TOKEN}
    r = requests.get(url, params=params)
    
    if r.status_code == 200:
        return r.json()
    return []

def format_cards(cards, prefix="  • "):
    if not cards:
        return "пусто"
    return "\n".join([f"{prefix}{c['name']}" for c in cards])

def morning_report():
    """Утренний отчёт: C1/C2 + C3 + Фокус Стратегия"""
    report = "☀️ УТРЕННИЙ ОТЧЁТ\n\n"
    
    # 1. C1/C2 Концепция
    p_prog = get_cards('production', 'inProgress')
    p_back = get_cards('production', 'backlog')
    
    report += "🎨 КОНЦЕПЦИЯ (C1/C2)\n"
    if p_prog:
        report += "В работе:\n" + format_cards(p_prog) + "\n"
    else:
        report += "В работе: пусто\n"
    report += f"Очередь: {len(p_back)} задач\n"
    
    # 2. C3 Рабочий проект
    c3_prog = get_cards('c3', 'inProgress')
    c3_back = get_cards('c3', 'backlog')
    
    report += "\n🏗️ РАБОЧИЙ ПРОЕКТ (C3)\n"
    if c3_prog:
        report += "В работе:\n" + format_cards(c3_prog) + "\n"
    else:
        report += "В работе: пусто\n"
    report += f"Очередь: {len(c3_back)} задач\n"

    # 3. Стратегия
    s_month = get_cards('strategy', 'этот_месяц')
    s_impl = get_cards('strategy', 'внедряю')
    
    report += "\n🎯 СТРАТЕГИЯ\n"
    report += "📅 Месяц:\n" + format_cards(s_month) + "\n"
    if s_impl:
        report += "🔄 Внедряю:\n" + format_cards(s_impl) + "\n"
    
    return report

def evening_report():
    """Вечерний отчёт: Итоги дня (C1/C2 + C3)"""
    report = "🌙 ВЕЧЕРНИЙ ОТЧЁТ\n\n"
    
    # C1/C2
    p_done = get_cards('production', 'done')
    p_prog = get_cards('production', 'inProgress')
    
    report += "🎨 КОНЦЕПЦИЯ (C1/C2)\n"
    report += "✅ Готово:\n" + format_cards(p_done) + "\n"
    if p_prog:
        report += f"🔄 В работе: {len(p_prog)} задач\n"
    
    # C3
    c3_done = get_cards('c3', 'done')
    c3_prog = get_cards('c3', 'inProgress')
    
    report += "\n🏗️ РАБОЧИЙ ПРОЕКТ (C3)\n"
    report += "✅ Готово:\n" + format_cards(c3_done) + "\n"
    if c3_prog:
        report += f"🔄 В работе: {len(c3_prog)} задач\n"
    
    # Стратегия
    s_impl = get_cards('strategy', 'внедряю')
    report += "\n🎯 СТРАТЕГИЯ\n"
    if s_impl:
        report += "🔄 Внедряю:\n" + format_cards(s_impl) + "\n"
        report += "\n💡 Двигай карточки в Стратегии перед сном\n"
    else:
        report += "Внедряю: пусто\n"
    
    return report

def quick_status():
    """Быстрый статус всех досок"""
    p_prog = get_cards('production', 'inProgress')
    c3_prog = get_cards('c3', 'inProgress')
    s_impl = get_cards('strategy', 'внедряю')
    
    report = "📊 СТАТУС\n\n"
    report += f"🎨 C1/C2: {len(p_prog)} в работе\n"
    report += f"🏗️ C3:    {len(c3_prog)} в работе\n"
    report += f"🎯 Strat: {len(s_impl)} внедряю\n"
    
    return report

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: trello-report.py [morning|evening|status|hourly]")
        sys.exit(1)
    
    cmd = sys.argv[1].replace('--', '') # Handle --flag style too
    
    if cmd == 'morning':
        print(morning_report())
    elif cmd == 'evening':
        print(evening_report())
    elif cmd == 'status' or cmd == 'hourly':
        print(quick_status())
    else:
        print(f"Unknown command: {cmd}")
