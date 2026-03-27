#!/usr/bin/env python3
"""Создание карточек на доске C3 по Регламенту v1.0

Использование:
    python3 create-c3-card.py --type hall --name "Холл ЖК Москва" --executor "Мирас" --deadline "2026-02-28"
    python3 create-c3-card.py --type apartment --name "Квартира 5к" --executor "Бахытжан" --deadline "2026-03-01"
    python3 create-c3-card.py --type airport --name "Аэропорт" --executor "Мирас" --deadline "2026-02-21"

Типы проектов:
    hall       - Холл ЖК
    apartment  - Квартира
    airport    - Аэропорт
    landscaping - Благоустройство
"""
import argparse
import requests
import json

# Загружаем конфиг
with open('/home/axis/openclaw/trello-config.json') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
BOARD_ID = config['boards']['c3']['id']
LISTS = config['boards']['c3']['lists']

# ID участников
MEMBERS = {
    'ruslan': '5b0b621494516d1ba0442af7',
    'miras': '69784343f3d43b670c56e76d',
    'bakhytzhan': '5feb25c46b886e7de90ea095',
}

# Чек-листы по типам проектов
CHECKLISTS = {
    'hall': {
        'name': 'Состав проекта (Холл ЖК)',
        'items': [
            'План обмеров (план исходный)',
            'План возводимых конструкций',
            'План отделки',
            'План потолка',
            'План привязки светильников',
            'План подключения светильников',
            'План полов. Экспликация полов',
            'План полов. Схема облицовки лестничного марша',
            'Рекомендации по заполнению дверных проёмов',
            'Развёртки стен (всех помещений)',
            'Ведомость отделки',
            'Ведомость оборудования',
        ]
    },
    'apartment': {
        'name': 'Состав проекта (Квартира)',
        'items': [
            'План обмеров',
            'План демонтажа',
            'План монтажа',
            'План отделки',
            'План потолка',
            'План привязки светильников',
            'План подключения светильников',
            'План полов',
            'Развёртки стен',
            'Ведомость отделки',
            'Ведомость оборудования',
        ]
    },
    'airport': {
        'name': 'Состав проекта (Интерьер)',
        'items': [
            'План обмеров (план исходный)',
            'План отделки',
            'План потолка',
            'План привязки светильников',
            'План подключения светильников',
            'План полов. Экспликация полов',
            'Развёртки стен (всех помещений)',
            'Ведомость отделки',
            'Ведомость оборудования',
        ]
    },
    'landscaping': {
        'name': 'Состав проекта (Благоустройство)',
        'items': [
            'Схема генплана',
            'Схема дорожно-тропиночной сети',
            'Схема озеленения',
            'Схема освещения',
            'Схема малых архитектурных форм',
            'Ведомость покрытий',
            'Ведомость озеленения',
            'Ведомость оборудования',
        ]
    }
}

OKK_CHECKLIST = {
    'name': 'ОКК — Проверка качества',
    'items': [
        'Полнота: все листы чеклиста состава присутствуют в альбоме',
        'Рамка: стандартная рамка OpenClaw.ai на каждом листе',
        'Штамп: заполнен (название проекта, номер листа, дата, автор)',
        'Масштаб: указан и соответствует содержанию чертежа',
        'Размерные цепочки: все размеры проставлены, цепочки замкнуты',
        'Выноски материалов: все материалы имеют выноски с артикулами',
        'Шрифты: единый шрифт и размер по стандарту',
        'Толщины линий: соответствуют стандарту оформления',
        'Развёртки: привязаны к планам, совпадают обозначения стен',
        'Расчёт материалов: объёмы в ведомости совпадают с площадями на чертежах',
        'Расчёт оборудования: количество светильников/сантехники совпадает с планами',
        'Нумерация листов: сквозная, соответствует ведомости чертежей',
    ]
}

def create_card(name, project_type, executor, deadline, folder_url=None, critical=False):
    """Создать карточку по регламенту C3"""
    
    # Получаем чек-лист для типа проекта
    project_checklist = CHECKLISTS.get(project_type, CHECKLISTS['hall'])
    
    # Формируем описание
    type_names = {
        'hall': 'Холл ЖК',
        'apartment': 'Квартира',
        'airport': 'Интерьер Аэропорта',
        'landscaping': 'Благоустройство'
    }
    
    desc = f"""{'🚨 **КРИТИЧЕСКИЙ ПРОЕКТ**' if critical else ''}

## Информация о проекте
- **Тип:** {type_names.get(project_type, project_type)}
- **Объект:** {name}
- **Исполнитель:** {executor}
- **Дедлайн:** {deadline}
- **Ссылка на папку:** {folder_url or '{добавить}'}

## Процесс (по регламенту C3)
1. Главный дизайнер готовит исходники → папка 01_Исходники
2. Архитектор чертит по порядку: планы → развёртки → ведомости
3. Архитектор отмечает чеклист и переносит карточку в «На проверку»
4. Главный дизайнер проверяет по чеклисту ОКК
5. Если правки — файл в 04_Правки, карточка в «Правки»
6. Если ОК — карточка в «Готово», PDF в 03_Выгрузка_PDF

## Правила
⚠️ Не начинать работу без полного комплекта исходников
⚠️ Правки передаются ТОЛЬКО через файл в 04_Правки, не устно
⚠️ Проект сдан когда ВСЕ пункты обоих чеклистов отмечены
"""
    
    # Создаём карточку
    url = 'https://api.trello.com/1/cards'
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'idList': LISTS['inProgress']['id'] if critical else LISTS['backlog']['id'],
        'name': f"{'🚨 ' if critical else ''}{name}",
        'desc': desc,
        'due': f"{deadline}T18:00:00.000Z",
        'pos': 'top'
    }
    
    r = requests.post(url, params=params)
    if r.status_code != 200:
        print(f"❌ Ошибка создания карточки: {r.text}")
        return None
    
    card = r.json()
    card_id = card['id']
    print(f"✅ Карточка создана: {card['shortUrl']}")
    
    # Добавляем участников
    member_id = MEMBERS.get(executor.lower())
    if member_id:
        url = f'https://api.trello.com/1/cards/{card_id}/idMembers'
        requests.post(url, params={'key': API_KEY, 'token': TOKEN, 'value': member_id})
        print(f"   👤 Назначен: {executor}")
    
    # Создаём чек-лист "Состав проекта"
    url = 'https://api.trello.com/1/checklists'
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'idCard': card_id,
        'name': project_checklist['name']
    }
    r = requests.post(url, params=params)
    if r.status_code == 200:
        checklist_id = r.json()['id']
        for item in project_checklist['items']:
            url = f'https://api.trello.com/1/checklists/{checklist_id}/checkItems'
            requests.post(url, params={'key': API_KEY, 'token': TOKEN, 'name': item})
        print(f"   📋 Добавлен чек-лист: {project_checklist['name']} ({len(project_checklist['items'])} пунктов)")
    
    # Создаём чек-лист "ОКК"
    url = 'https://api.trello.com/1/checklists'
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'idCard': card_id,
        'name': OKK_CHECKLIST['name']
    }
    r = requests.post(url, params=params)
    if r.status_code == 200:
        checklist_id = r.json()['id']
        for item in OKK_CHECKLIST['items']:
            url = f'https://api.trello.com/1/checklists/{checklist_id}/checkItems'
            requests.post(url, params={'key': API_KEY, 'token': TOKEN, 'name': item})
        print(f"   📋 Добавлен чек-лист: {OKK_CHECKLIST['name']} ({len(OKK_CHECKLIST['items'])} пунктов)")
    
    return card

def main():
    parser = argparse.ArgumentParser(description='Создание карточек C3 по регламенту')
    parser.add_argument('--type', required=True, choices=['hall', 'apartment', 'airport', 'landscaping'],
                        help='Тип проекта')
    parser.add_argument('--name', required=True, help='Название объекта')
    parser.add_argument('--executor', required=True, help='Исполнитель (Мирас, Бахытжан, Руслан)')
    parser.add_argument('--deadline', required=True, help='Дедлайн (YYYY-MM-DD)')
    parser.add_argument('--folder', help='Ссылка на папку проекта')
    parser.add_argument('--critical', action='store_true', help='Критический проект')
    
    args = parser.parse_args()
    
    print(f"\n📝 Создаю карточку: {args.name}")
    print(f"   Тип: {args.type}")
    print(f"   Исполнитель: {args.executor}")
    print(f"   Дедлайн: {args.deadline}")
    print()
    
    card = create_card(
        name=args.name,
        project_type=args.type,
        executor=args.executor,
        deadline=args.deadline,
        folder_url=args.folder,
        critical=args.critical
    )
    
    if card:
        print(f"\n{'='*60}")
        print(f"✅ Карточка создана по регламенту C3!")
        print(f"🔗 {card['shortUrl']}")
        print('='*60)

if __name__ == '__main__':
    main()
