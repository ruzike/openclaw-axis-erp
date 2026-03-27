import json
import requests
import sys

CARD_ID = '69896df8e0a9c116e288f93d' # Эм... Стоп, это ID доски. Нужно найти ID карточки.
# ID карточки из лога: 'oXgd7Ru1' (ShortLink). Полный ID нужно найти.

# 1. Сначала найдем ID созданной карточки по ShortLink
# ... или просто воспользуемся тем, что create вернул
# А, стоп, мой create возвращает JSON

# Давайте так: я сейчас напишу скрипт, который проапдейтит карточку по ShortLink
# (Trello API умеет working with ShortLink)

SHORT_LINK = 'oXgd7Ru1'  # Из лога
MEMBER_ID = '5b0b621494516d1ba0442af7' # Ruslan
DUE_DATE = '2026-02-26T12:00:00.000Z' # Среда, полдень

with open('/home/axis/openclaw/trello-config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['api']['key']
TOKEN = config['api']['token']

url = f"https://api.trello.com/1/cards/{SHORT_LINK}"
params = {
    'key': API_KEY,
    'token': TOKEN,
    'idMembers': MEMBER_ID,
    'due': DUE_DATE
}

r = requests.put(url, params=params)
if r.status_code == 200:
    print("✅ Карточка обновлена (Ответственный + Дедлайн)!")
else:
    print(f"❌ Ошибка обновления: {r.text}")
