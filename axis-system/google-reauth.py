#!/usr/bin/env python3
"""
Google Forms OAuth2 — переавторизация.
Запусти: python3 google-reauth.py
Вставь authorization code когда попросит.
"""
import json, urllib.request, urllib.parse, os

CREDS_PATH = os.path.expanduser('~/.openclaw/credentials/google-forms-oauth.json')

with open(CREDS_PATH) as f:
    creds = json.load(f)

CLIENT_ID = creds['client_id']
CLIENT_SECRET = creds['client_secret']
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
SCOPES = ['https://www.googleapis.com/auth/forms', 'https://www.googleapis.com/auth/drive']

auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode({
    'client_id': CLIENT_ID,
    'redirect_uri': REDIRECT_URI,
    'response_type': 'code',
    'scope': ' '.join(SCOPES),
    'access_type': 'offline',
    'prompt': 'consent'
})

print("\n=== Google Forms OAuth2 Reauthorization ===\n")
print("1. Открой эту ссылку в браузере:")
print(f"\n{auth_url}\n")
print("2. Войди в нужный Google аккаунт")
print("3. Разреши доступ к Forms и Drive")
print("4. Скопируй код авторизации и вставь ниже\n")

code = input("Authorization code: ").strip()

# Обмениваем code на tokens
data = urllib.parse.urlencode({
    'code': code,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI,
    'grant_type': 'authorization_code'
}).encode()

try:
    req = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        tokens = json.loads(resp.read())

    if 'refresh_token' not in tokens:
        print("❌ refresh_token не получен. Попробуй снова (убедись что prompt=consent)")
        exit(1)

    # Сохраняем новые credentials
    new_creds = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': tokens['refresh_token'],
        'type': 'authorized_user'
    }
    with open(CREDS_PATH, 'w') as f:
        json.dump(new_creds, f, indent=2)
    os.chmod(CREDS_PATH, 0o600)

    print(f"\n✅ Готово! Новый refresh_token сохранён в {CREDS_PATH}")
    print(f"   access_token (temporary): {tokens.get('access_token','')[:30]}...")
    print(f"   expires_in: {tokens.get('expires_in')} сек")
    print("\nТеперь запусти: cd /home/axis/openclaw/skills/google-forms && GOOGLE_FORMS_CREDENTIALS=~/.openclaw/credentials/google-forms-oauth.json node google-forms.js list")

except urllib.error.HTTPError as e:
    body = json.loads(e.read())
    print(f"❌ Ошибка: {body}")
