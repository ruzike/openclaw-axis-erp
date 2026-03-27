#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import os

CREDENTIALS_FILE = '/home/axis/.config/gogcli/credentials.json'
TOKEN_FILE = '/home/axis/.config/gogcli/token-ruslanshakirzhanovich.json'
FOLDER_NAME = 'AXIS Coach Videos'

def get_token():
    with open(CREDENTIALS_FILE) as f:
        creds = json.load(f)
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    data = urllib.parse.urlencode({
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'refresh_token': token_data['refresh_token'],
        'grant_type': 'refresh_token',
    }).encode()

    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            new_token = json.loads(resp.read())
            return new_token['access_token']
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def create_folder(access_token):
    # Сначала ищем, нет ли уже такой папки
    q = urllib.parse.quote(f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false")
    req = urllib.request.Request(f'https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)')
    req.add_header('Authorization', f'Bearer {access_token}')
    
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read())
        if res.get('files'):
            print(f"Folder already exists. ID: {res['files'][0]['id']}")
            return res['files'][0]['id']

    # Если нет - создаём
    metadata = json.dumps({
        'name': FOLDER_NAME,
        'mimeType': 'application/vnd.google-apps.folder'
    }).encode()

    req = urllib.request.Request('https://www.googleapis.com/drive/v3/files', data=metadata, method='POST')
    req.add_header('Authorization', f'Bearer {access_token}')
    req.add_header('Content-Type', 'application/json')
    
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read())
        print(f"Created folder. ID: {res['id']}")
        return res['id']

if __name__ == '__main__':
    token = get_token()
    if token:
        folder_id = create_folder(token)
        if folder_id:
            with open('/home/axis/openclaw/agents/coach/gdrive-folder-id.txt', 'w') as f:
                f.write(folder_id)
            print("Folder ID saved to gdrive-folder-id.txt")
