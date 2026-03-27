import requests
import sys
import json

BOT_TOKEN = "8387135726:AAEx-QtfakT4nwaVUb9a4AFtPVReIdfoVos"
CHANNEL = "@neuro_dir"

def get_post_info(message_id):
    """Копируем сообщение к себе чтобы узнать его тип"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"
    data = {
        'chat_id': YOUR_TELEGRAM_ID,
        'from_chat_id': CHANNEL,
        'message_id': message_id
    }
    r = requests.post(url, data=data)
    return r.json()

def edit_caption(message_id, new_caption):
    """Редактируем caption у фото-поста"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageCaption"
    data = {
        'chat_id': CHANNEL,
        'message_id': message_id,
        'caption': new_caption,
        'parse_mode': 'Markdown'
    }
    r = requests.post(url, data=data)
    return r.json()

def edit_text(message_id, new_text):
    """Редактируем текстовый пост"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    data = {
        'chat_id': CHANNEL,
        'message_id': message_id,
        'text': new_text,
        'parse_mode': 'Markdown'
    }
    r = requests.post(url, data=data)
    return r.json()

def delete_message(message_id):
    """Удаляем сообщение"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
    data = {
        'chat_id': CHANNEL,
        'message_id': message_id
    }
    r = requests.post(url, data=data)
    return r.json()

def send_photo(photo_path, caption):
    """Отправляем фото с caption"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        data = {'chat_id': CHANNEL, 'caption': caption, 'parse_mode': 'Markdown'}
        r = requests.post(url, files=files, data=data)
    return r.json()

if __name__ == "__main__":
    action = sys.argv[1]
    msg_id = int(sys.argv[2])
    
    if action == "edit_caption":
        text = sys.argv[3]
        result = edit_caption(msg_id, text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif action == "edit_text":
        text = sys.argv[3]
        result = edit_text(msg_id, text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif action == "delete":
        result = delete_message(msg_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif action == "info":
        result = get_post_info(msg_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
