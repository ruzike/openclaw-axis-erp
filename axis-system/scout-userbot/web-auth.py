#!/usr/bin/env python3
"""Web-based Pyrogram auth — user enters code directly, no delay"""
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from pyrogram import Client

API_ID = 30753988
API_HASH = "834c894a81de6018616ef961f7cc404e"
PHONE = "+77713926440"
PORT = 18796
WORKDIR = "/home/axis/openclaw/axis-system/scout-userbot"

code_future = None
loop = None
result_text = "waiting..."

HTML_FORM = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AXIS Scout Auth</title>
<style>body{font-family:system-ui;max-width:400px;margin:50px auto;padding:20px}
input{font-size:24px;padding:10px;width:100%;text-align:center;margin:10px 0}
button{font-size:20px;padding:10px 30px;background:#0088cc;color:white;border:none;border-radius:5px;cursor:pointer;width:100%}
.status{margin-top:20px;padding:15px;background:#f0f0f0;border-radius:5px}</style></head>
<body><h2>🔐 AXIS Scout Auth</h2>
<p>Код отправлен в Telegram на +7 771 392 64 40</p>
<p>Введи код:</p>
<form method="POST" action="/code">
<input type="text" name="code" maxlength="5" pattern="[0-9]{5}" autofocus placeholder="12345">
<button type="submit">Подтвердить</button>
</form>
<div class="status">STATUS</div></body></html>"""

HTML_OK = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>body{font-family:system-ui;max-width:400px;margin:50px auto;padding:20px;text-align:center}</style></head>
<body><h2>✅ Авторизация успешна!</h2><p>RESULT</p><p>Можешь закрыть эту страницу.</p></body></html>"""

HTML_ERR = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>body{font-family:system-ui;max-width:400px;margin:50px auto;padding:20px;text-align:center}</style></head>
<body><h2>❌ Ошибка</h2><p>ERROR</p><p><a href="/">Попробовать снова</a></p></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_FORM.replace("STATUS", result_text).encode())

    def do_POST(self):
        global result_text
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)
        code = params.get("code", [""])[0].strip()

        if code and code_future and not code_future.done():
            loop.call_soon_threadsafe(code_future.set_result, code)
            # Wait a bit for result
            import time
            time.sleep(3)
            if "OK" in result_text:
                html = HTML_OK.replace("RESULT", result_text)
            else:
                html = HTML_ERR.replace("ERROR", result_text)
        else:
            html = HTML_ERR.replace("ERROR", "No pending auth or empty code")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, *args):
        pass


async def auth():
    global code_future, loop, result_text
    loop = asyncio.get_event_loop()

    app = Client(
        "axis_scout",
        api_id=API_ID,
        api_hash=API_HASH,
        workdir=WORKDIR,
        phone_number=PHONE,
        phone_code=get_code
    )

    try:
        await app.start()
        me = await app.get_me()
        result_text = f"OK: {me.first_name} (id: {me.id})"
        print(f"✅ {result_text}")
        await app.stop()
    except Exception as e:
        result_text = f"Error: {e}"
        print(f"❌ {result_text}")


async def get_code():
    global code_future
    code_future = asyncio.get_event_loop().create_future()
    print("⏳ Waiting for code on web form...")
    code = await code_future
    print(f"📨 Code received: {code}")
    return code


def run_server():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"🌐 Auth page: http://89.167.124.79:{PORT}/")
    server.serve_forever()


if __name__ == "__main__":
    import os
    os.chdir(WORKDIR)
    # Remove old session
    for f in os.listdir(WORKDIR):
        if f.endswith(".session"):
            os.remove(os.path.join(WORKDIR, f))

    # Start web server in background
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    # Run auth
    asyncio.run(auth())
    print("Done. Exiting in 10s...")
    import time
    time.sleep(10)
