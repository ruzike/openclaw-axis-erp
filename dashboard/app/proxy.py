#!/usr/bin/env python3
"""Tiny CORS proxy: serves static PWA + proxies /v1/* to Gateway"""
from flask import Flask, request, Response, send_from_directory
import requests
import os

app = Flask(__name__)
GATEWAY = "http://127.0.0.1:18789"
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.dirname(STATIC_DIR)

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/v1/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def proxy_api(path):
    if request.method == 'OPTIONS':
        return Response('', 200)
    resp = requests.request(
        method=request.method,
        url=f"{GATEWAY}/v1/{path}",
        headers={k: v for k, v in request.headers if k.lower() in ('authorization', 'content-type')},
        data=request.get_data(),
        timeout=120
    )
    return Response(resp.content, resp.status_code, {'Content-Type': resp.headers.get('Content-Type', 'application/json')})

@app.route('/health')
def health():
    try:
        r = requests.get(f"http://127.0.0.1:18795/health", timeout=5)
        return Response(r.content, r.status_code, {'Content-Type': 'application/json'})
    except:
        return Response('{"status":"error"}', 500)

# Dashboard files
@app.route('/dashboards/<path:filename>')
def dashboard(filename):
    return send_from_directory(DASHBOARD_DIR, filename)

# PWA static
@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=18801, debug=False)
