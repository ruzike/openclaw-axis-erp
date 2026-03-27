#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import os, urllib.parse

UPLOAD_DIR = '/home/axis/openclaw/dashboard/snaps'
os.makedirs(UPLOAD_DIR, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    def do_PUT(self):
        path = urllib.parse.unquote(self.path.lstrip('/'))
        filename = os.path.basename(path)
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(data)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')
        print(f'Saved: {filepath} ({len(data)} bytes)')

    def log_message(self, fmt, *args):
        print(fmt % args)

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 19001), Handler)
    print('Upload server on :19001')
    server.serve_forever()
