#!/usr/bin/env python3
"""Добавить метки к проектам"""
import requests
import json

with open('/home/axis/openclaw/trello-config.json') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']
BOARD_ID = config['boards']['production']['id']

# ID меток
LABEL_CRITICAL = '6981d92a2e52fda8adfae0f0'
LABEL_MEDIUM = '6981d92b21b31c8e581da52d'

# Карточки с их ID (shortUrl последние 8 символов)
cards_labels = [
    ('CuQPrkR2', ['critical', 'medium']),  # ЖК ТОКИО
    ('PJiasvDh', ['critical']),  # АЭРОПОРТ
    ('tFFPkjmE', ['critical', 'medium']),  # ЖК ЛОНДОН
    ('AQJMEsSr', ['critical']),  # ЕСИЛЬ СИТИ 2
    ('gL5Mz794', ['critical', 'medium']),  # СЭД ОФИС
    ('B2rR3iNZ', ['critical', 'medium']),  # СЭД Костанай
    ('DGrIaeUF', ['critical', 'medium']),  # СЭД П-павловск
    ('lsBPCl3G', ['medium']),  # Австрийский 4
]

def add_label_to_card(card_short_id, label_type):
    """Добавить метку к карточке"""
    label_id = LABEL_CRITICAL if label_type == 'critical' else LABEL_MEDIUM
    
    url = f'https://api.trello.com/1/cards/{card_short_id}/idLabels'
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'value': label_id
    }
    
    r = requests.post(url, params=params)
    return r.status_code == 200

for card_id, labels in cards_labels:
    for label in labels:
        emoji = '🔴' if label == 'critical' else '🟡'
        if add_label_to_card(card_id, label):
            print(f"✅ {emoji} → {card_id}")
        else:
            print(f"❌ Ошибка → {card_id}")

print("\n✅ Метки добавлены!")
