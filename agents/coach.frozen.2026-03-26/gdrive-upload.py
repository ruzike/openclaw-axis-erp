#!/usr/bin/env python3
"""
Google Drive upload script for AXIS Coach agent.
Usage: python3 gdrive-upload.py /path/to/file.mp4 [Title/Name]
Returns: public link to uploaded file
"""

import sys
import json
import os
import urllib.request
import urllib.parse
import mimetypes

CREDENTIALS_FILE = '/home/axis/.config/gogcli/credentials.json'
TOKEN_FILE = '/home/axis/.config/gogcli/token-ruslanshakirzhanovich.json'
FOLDER_ID_FILE = '/home/axis/openclaw/agents/coach/gdrive-folder-id.txt'

def get_access_token():
    with open(CREDENTIALS_FILE) as f:
        creds = json.load(f)
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    data = urllib.parse.urlencode({
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'refresh_token': token_data['refresh_token'],
        'grant_type': 'refresh_token',
    }).encode('utf-8')

    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            new_token = json.loads(resp.read())
            token_data['access_token'] = new_token['access_token']
            with open(TOKEN_FILE, 'w') as f:
                json.dump(token_data, f)
            return new_token['access_token']
    except Exception as e:
        print(f"Error getting access token: {e}", file=sys.stderr)
        sys.exit(1)

def upload_file(file_path, custom_name=None):
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(FOLDER_ID_FILE) as f:
            folder_id = f.read().strip()
    except Exception:
        print("ERROR: Folder ID file not found. Run create-folder.py first.", file=sys.stderr)
        sys.exit(1)

    access_token = get_access_token()
    filename = custom_name if custom_name else os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'application/octet-stream'

    # Metadata
    metadata = json.dumps({
        'name': filename,
        'parents': [folder_id]
    }).encode('utf-8')

    with open(file_path, 'rb') as f:
        file_data = f.read()

    # Multipart upload
    boundary = 'axis_coach_boundary_123456'
    
    body = bytearray()
    body += f'--{boundary}\r\n'.encode('utf-8')
    body += f'Content-Type: application/json; charset=UTF-8\r\n\r\n'.encode('utf-8')
    body += metadata + b'\r\n'
    body += f'--{boundary}\r\n'.encode('utf-8')
    body += f'Content-Type: {mime_type}\r\n\r\n'.encode('utf-8')
    body += file_data + b'\r\n'
    body += f'--{boundary}--'.encode('utf-8')

    req = urllib.request.Request(
        'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink',
        data=body,
        method='POST'
    )
    req.add_header('Authorization', f'Bearer {access_token}')
    req.add_header('Content-Type', f'multipart/related; boundary={boundary}')

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
            file_id = result['id']
            link = result.get('webViewLink', f'https://drive.google.com/file/d/{file_id}/view')
    except Exception as e:
        print(f"Error uploading file: {e}", file=sys.stderr)
        sys.exit(1)

    # Делаем файл доступным по ссылке (чтобы Руслан мог открыть его)
    try:
        perm_data = json.dumps({'role': 'reader', 'type': 'anyone'}).encode('utf-8')
        perm_req = urllib.request.Request(
            f'https://www.googleapis.com/drive/v3/files/{file_id}/permissions',
            data=perm_data,
            method='POST'
        )
        perm_req.add_header('Authorization', f'Bearer {access_token}')
        perm_req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(perm_req, timeout=15) as resp:
            pass
    except Exception as e:
        print(f"Warning: Could not set permissions: {e}", file=sys.stderr)

    print(link)
    return link

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 gdrive-upload.py <file_path> [Custom_Name]", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    custom_name = sys.argv[2] if len(sys.argv) > 2 else None
    upload_file(file_path, custom_name)
