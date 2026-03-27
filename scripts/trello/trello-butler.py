#!/usr/bin/env python3
"""
Trello Butler — автоматизация правил для Trello
Функции: daily_reminder, overdue_check, weekly_report, retrospective_reminder, transfer_wip

Использование:
  python3 trello-butler.py daily_reminder
  python3 trello-butler.py overdue_check
  python3 trello-butler.py weekly_report
  python3 trello-butler.py retrospective_reminder
  python3 trello-butler.py transfer_wip
"""

import json
import sys
import requests
from datetime import datetime, timezone, timedelta

# --- Config ---
CONFIG_PATH = '/home/axis/openclaw/trello-config.json'
TZ = timezone(timedelta(hours=5))  # Asia/Qyzylorda GMT+5
WIP_LIMIT = 5  # макс карточек в "Сегодня"

try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
except Exception as e:
    print(f"❌ Не удалось загрузить конфиг: {e}")
    sys.exit(1)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
BOARDS = config['boards']
MEMBERS = config.get('members', {})

# Telegram (Руслан)
TELEGRAM_BOT_TOKEN = None  # заполняется из env или вручную
TELEGRAM_CHAT_ID = MEMBERS.get('ruslan', {}).get('telegram_id', YOUR_TELEGRAM_ID)


def trello_get(endpoint, params=None):
    """GET-запрос к Trello API с обработкой ошибок"""
    url = f"https://api.trello.com/1/{endpoint}"
    p = {'key': API_KEY, 'token': TOKEN}
    if params:
        p.update(params)
    try:
        r = requests.get(url, params=p, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"❌ Trello API ошибка [{endpoint}]: {e}")
        return None


def trello_put(endpoint, params=None):
    """PUT-запрос к Trello API"""
    url = f"https://api.trello.com/1/{endpoint}"
    p = {'key': API_KEY, 'token': TOKEN}
    if params:
        p.update(params)
    try:
        r = requests.put(url, params=p, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"❌ Trello PUT ошибка [{endpoint}]: {e}")
        return None


def get_list_cards(board_key, list_key):
    """Получить карточки из колонки"""
    board = BOARDS.get(board_key)
    if not board:
        print(f"❌ Доска '{board_key}' не найдена")
        return []
    lst = board['lists'].get(list_key)
    if not lst:
        print(f"❌ Колонка '{list_key}' не найдена на '{board_key}'")
        return []
    cards = trello_get(f"lists/{lst['id']}/cards", {'fields': 'name,due,dueComplete,idMembers,shortUrl,labels'})
    return cards or []


def send_telegram(text):
    """Отправить сообщение в Telegram. Выводит в stdout если нет бота."""
    print(text)
    if TELEGRAM_BOT_TOKEN:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': text,
                'parse_mode': 'Markdown'
            }, timeout=10)
        except Exception as e:
            print(f"⚠️ Telegram ошибка: {e}")


def now_local():
    return datetime.now(TZ)


# ============================================================
# 1. daily_reminder — напоминание перед Daily (08:45)
# ============================================================
def daily_reminder():
    """Напоминание перед Daily: показать задачи в 'Сегодня' и 'В работе'"""
    today_cards = get_list_cards('production', 'today')
    wip_cards = get_list_cards('production', 'inProgress')

    lines = ["🌅 *Daily Reminder*\n"]

    if today_cards:
        lines.append(f"📋 *Сегодня* ({len(today_cards)}):")
        for c in today_cards:
            due_str = ""
            if c.get('due'):
                due_str = f" ⏰ {c['due'][:10]}"
            lines.append(f"  • {c['name']}{due_str}")
    else:
        lines.append("📋 *Сегодня*: пусто")

    if wip_cards:
        lines.append(f"\n🔄 *В работе* ({len(wip_cards)}):")
        for c in wip_cards:
            lines.append(f"  • {c['name']}")

    lines.append(f"\n⏰ Daily начинается скоро. Подготовься!")
    send_telegram("\n".join(lines))


# ============================================================
# 2. overdue_check — проверка просроченных задач (09:30, 18:30)
# ============================================================
def overdue_check():
    """Проверить просроченные задачи на всех досках"""
    now = datetime.now(timezone.utc)
    overdue = []

    for board_key, board in BOARDS.items():
        for list_key, lst in board['lists'].items():
            # Пропускаем "Готово" и "Не актуально"
            if list_key in ('done', 'notRelevant'):
                continue
            cards = trello_get(f"lists/{lst['id']}/cards", {'fields': 'name,due,dueComplete,shortUrl'})
            if not cards:
                continue
            for c in cards:
                if c.get('due') and not c.get('dueComplete'):
                    try:
                        due_dt = datetime.fromisoformat(c['due'].replace('Z', '+00:00'))
                        if due_dt < now:
                            overdue.append({
                                'name': c['name'],
                                'due': c['due'][:10],
                                'board': board.get('name', board_key),
                                'url': c.get('shortUrl', '')
                            })
                    except (ValueError, KeyError):
                        pass

    if overdue:
        lines = [f"🚨 *Просроченные задачи* ({len(overdue)}):\n"]
        for o in overdue:
            lines.append(f"• *{o['name']}* — срок {o['due']}")
            lines.append(f"  📍 {o['board']} | {o['url']}")
        send_telegram("\n".join(lines))
    else:
        send_telegram("✅ Просроченных задач нет!")


# ============================================================
# 3. weekly_report — пятничный отчёт (17:00 пятница)
# ============================================================
def weekly_report():
    """Недельный отчёт: сколько задач в каждой колонке"""
    lines = ["📊 *Еженедельный отчёт*\n"]

    for board_key, board in BOARDS.items():
        lines.append(f"🎯 *{board.get('name', board_key)}*:")
        total = 0
        for list_key, lst in board['lists'].items():
            cards = trello_get(f"lists/{lst['id']}/cards", {'fields': 'id'})
            count = len(cards) if cards else 0
            total += count
            lines.append(f"  • {lst['name']}: {count}")
        lines.append(f"  📈 Итого: {total}\n")

    # Done за неделю (production)
    done_cards = get_list_cards('production', 'done')
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_done = []
    for c in done_cards:
        # Проверяем через actions, но для простоты считаем все в Done
        recent_done.append(c['name'])

    if recent_done:
        lines.append(f"✅ *Завершено* (в 'Готово'): {len(recent_done)}")
        for name in recent_done[:10]:
            lines.append(f"  • {name}")

    send_telegram("\n".join(lines))


# ============================================================
# 4. retrospective_reminder — напоминание о ретро (28-е число)
# ============================================================
def retrospective_reminder():
    """Напоминание о ретроспективе 28 числа каждого месяца"""
    today = now_local()
    lines = [
        "🔄 *Напоминание: Ретроспектива*\n",
        f"📅 Сегодня {today.strftime('%d.%m.%Y')} — день ретроспективы!\n",
        "Подготовь ответы на:",
        "1️⃣ Что получилось хорошо?",
        "2️⃣ Что можно улучшить?",
        "3️⃣ Какие решения принимаем?\n",
        "📋 Проверь доску *Стратегия* → колонка *Внедряю*"
    ]

    # Показать что во "Внедряю"
    impl_cards = get_list_cards('strategy', 'внедряю')
    if impl_cards:
        lines.append(f"\n🔄 *Сейчас внедряется* ({len(impl_cards)}):")
        for c in impl_cards:
            lines.append(f"  • {c['name']}")

    send_telegram("\n".join(lines))


# ============================================================
# 5. transfer_wip — лимит WIP, перенос из "Сегодня" если >5
# ============================================================
def transfer_wip():
    """Проверить WIP-лимит в 'Сегодня'. Если >5 — переместить лишние в 'Очередь'"""
    today_cards = get_list_cards('production', 'today')
    count = len(today_cards)

    if count <= WIP_LIMIT:
        send_telegram(f"✅ WIP в норме: {count}/{WIP_LIMIT} задач в 'Сегодня'")
        return

    excess = count - WIP_LIMIT
    backlog_list_id = BOARDS['production']['lists']['backlog']['id']

    lines = [f"⚠️ *WIP превышен*: {count}/{WIP_LIMIT} в 'Сегодня'\n"]
    lines.append(f"Переношу {excess} задач(и) в 'Очередь':\n")

    # Переносим последние (нижние) карточки
    to_move = today_cards[-excess:]
    moved = 0
    for card in to_move:
        result = trello_put(f"cards/{card['id']}", {'idList': backlog_list_id})
        if result:
            lines.append(f"  ↩️ {card['name']}")
            moved += 1
        else:
            lines.append(f"  ❌ Не удалось: {card['name']}")

    lines.append(f"\n📊 Перенесено: {moved}/{excess}")
    send_telegram("\n".join(lines))


# ============================================================
# CLI
# ============================================================
COMMANDS = {
    'daily_reminder': daily_reminder,
    'overdue_check': overdue_check,
    'weekly_report': weekly_report,
    'retrospective_reminder': retrospective_reminder,
    'transfer_wip': transfer_wip,
}

if __name__ == '__main__':
    import os
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

    if len(sys.argv) < 2:
        print("Trello Butler — автоматизация\n")
        print("Команды:")
        for cmd in COMMANDS:
            print(f"  python3 trello-butler.py {cmd}")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd in COMMANDS:
        print(f"🤖 Запуск: {cmd} | {now_local().strftime('%Y-%m-%d %H:%M')}")
        print("-" * 40)
        COMMANDS[cmd]()
    else:
        print(f"❌ Неизвестная команда: {cmd}")
        print(f"Доступные: {', '.join(COMMANDS.keys())}")
        sys.exit(1)
