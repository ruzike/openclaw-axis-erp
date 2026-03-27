import os
import sys
import requests

# Токен шкета
BOT_TOKEN = "8387135726:AAEx-QtfakT4nwaVUb9a4AFtPVReIdfoVos"

def send_photo(chat_id, photo_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
        response = requests.post(url, files=files, data=data)
        
    if response.status_code == 200:
        print(f"✅ Успешно отправлено в {chat_id}")
    else:
        print(f"❌ Ошибка отправки: {response.text}")

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        print(f"✅ Успешно отправлено в {chat_id}")
    else:
        print(f"❌ Ошибка отправки: {response.text}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python3 post_to_telegram.py <chat_id> [путь_к_фото] \"<текст_поста>\"")
        print("Если путь_к_фото не указан или пустой, отправляется только текстовое сообщение")
        sys.exit(1)
        
    chat_id = sys.argv[1]
    text = sys.argv[-1]  # Текст всегда последний аргумент
    
    # Проверяем, есть ли путь к фото и он не пустой
    if len(sys.argv) >= 4 and sys.argv[2]:
        photo_path = sys.argv[2]
        send_photo(chat_id, photo_path, text)
    else:
        send_message(chat_id, text)
