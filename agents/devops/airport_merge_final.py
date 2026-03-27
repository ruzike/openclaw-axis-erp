#!/usr/bin/env python3
"""
Final airport card merge: scan all lists, add old card names to checklist, delete old cards.
"""
import json, requests, time, sys

with open('/home/axis/openclaw/trello-config.json') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN   = config['api']['token']
BASE    = "https://api.trello.com/1"

BOARD        = config['boards']['production']
BOARD_ID     = BOARD['id']
IN_PROGRESS  = BOARD['lists']['inProgress']['id']
MAIN_ID      = "699870c8bdf24bdc08ac8b39"   # already created
MAIN_TITLE   = "Аэропорт Аркалык — Фасад Рабочка"
SEARCH_TERMS = ["аэро", "airport", "аркалык", "аэропорт"]

def q(method, path, **kw):
    kw.setdefault('params', {}).update(key=API_KEY, token=TOKEN)
    for i in range(5):
        r = getattr(requests, method)(BASE + path, **kw)
        if r.status_code == 429:
            t = int(r.headers.get('Retry-After', 10)) + i*5
            print(f"⏳ rate-limit {t}s", file=sys.stderr); time.sleep(t); continue
        return r
    return r

# ── 1. Scan every list for airport cards ─────────────────────────────────────
print("Scanning ALL lists for airport cards…")
found = {}   # id -> card dict

for lname, ldata in BOARD['lists'].items():
    r = q('get', f"/lists/{ldata['id']}/cards", params={'fields': 'name,id,idList,desc'})
    if r.status_code != 200:
        print(f"  ⚠ list {lname}: {r.text}"); continue
    for card in r.json():
        cn = card['name'].lower()
        if any(t in cn for t in SEARCH_TERMS):
            found[card['id']] = card
            print(f"  ✓ [{lname}] {card['name']} ({card['id']})")

print(f"\nFound {len(found)} airport card(s) total.")

# ── 2. Separate main card from the rest ──────────────────────────────────────
old_cards = {cid: c for cid, c in found.items() if cid != MAIN_ID}
print(f"Old cards to merge: {len(old_cards)}")

# ── 3. Build checklist items from old card names ─────────────────────────────
DEFAULT_ITEMS = [
    "Подготовка технического задания",
    "Разработка проекта фасада",
    "Получение согласований",
    "Заказ материалов",
    "Монтажные работы",
    "Финальная приемка",
]

checklist_items = list(DEFAULT_ITEMS)  # start with default
for c in old_cards.values():
    name = c['name'].strip()
    if name not in checklist_items and name != MAIN_TITLE:
        checklist_items.append(name)

# ── 4. Check existing checklists on main card ────────────────────────────────
print(f"\nChecking checklists on main card {MAIN_ID}…")
r = q('get', f"/cards/{MAIN_ID}/checklists")
existing_checklists = r.json() if r.status_code == 200 else []

if existing_checklists:
    print(f"  ℹ {len(existing_checklists)} checklist(s) already present — deleting them and recreating.")
    for cl in existing_checklists:
        dr = q('delete', f"/checklists/{cl['id']}")
        status = "✓ deleted" if dr.status_code == 200 else f"⚠ {dr.status_code}"
        print(f"  {status} checklist '{cl['name']}'")

# ── 5. Create fresh checklist ────────────────────────────────────────────────
print(f"\nCreating checklist 'Подзадачи' with {len(checklist_items)} items…")
r = q('post', "/checklists", params={'idCard': MAIN_ID, 'name': 'Подзадачи'})
if r.status_code != 200:
    print(f"❌ Failed to create checklist: {r.text}"); sys.exit(1)
cl_id = r.json()['id']

for item in checklist_items:
    r2 = q('post', f"/checklists/{cl_id}/checkItems",
            params={'name': item, 'pos': 'bottom'})
    status = "  ✓" if r2.status_code == 200 else f"  ⚠ {r2.status_code}"
    print(f"{status} {item}")

# ── 6. Move main card to В работе if it isn't already ───────────────────────
print(f"\nEnsuring main card is in 'В работе'…")
r = q('get', f"/cards/{MAIN_ID}", params={'fields': 'idList'})
if r.status_code == 200 and r.json()['idList'] != IN_PROGRESS:
    r2 = q('put', f"/cards/{MAIN_ID}", params={'idList': IN_PROGRESS})
    print("  ✓ moved" if r2.status_code == 200 else f"  ⚠ {r2.status_code}")
else:
    print("  ✓ already in 'В работе'")

# ── 7. Delete / archive old cards ────────────────────────────────────────────
print(f"\nArchiving {len(old_cards)} old airport card(s)…")
deleted = []
for cid, card in old_cards.items():
    r = q('put', f"/cards/{cid}", params={'closed': 'true'})
    if r.status_code == 200:
        deleted.append(card['name'])
        print(f"  ✓ archived: {card['name']}")
    else:
        print(f"  ⚠ failed to archive {card['name']}: {r.text}")

# ── 8. Final report ──────────────────────────────────────────────────────────
print("\n" + "="*60)
print("✅ DONE — ИТОГОВЫЙ ОТЧЁТ")
print("="*60)
print(f"Главная карточка : {MAIN_TITLE}")
print(f"ID               : {MAIN_ID}")
print(f"Список           : В работе")
print(f"Чеклист пунктов  : {len(checklist_items)}")
print()
print(f"Найдено аэро-карточек: {len(found)}")
print(f"Заархивировано       : {len(deleted)}")
if deleted:
    for n in deleted:
        print(f"  — {n}")
print("="*60)
