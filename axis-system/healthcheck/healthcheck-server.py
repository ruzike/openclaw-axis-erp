#!/usr/bin/env python3
"""
AXIS Healthcheck Server
Единый эндпоинт для проверки всех компонентов системы.
Порт: 18795

GET /health        → полный статус (JSON)
GET /health/ping   → быстрый "ok" для UptimeRobot
"""

import http.server
import json
import subprocess
import os
import shutil
from datetime import datetime

PORT = 18795


def check_process(name, search):
    """Проверить запущен ли процесс"""
    try:
        result = subprocess.run(['pgrep', '-f', search], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def check_port(port):
    """Проверить слушает ли порт"""
    try:
        result = subprocess.run(
            ['ss', '-tlnp', f'src :{port}'],
            capture_output=True, text=True, timeout=5
        )
        return str(port) in result.stdout
    except Exception:
        return False


def get_disk_usage():
    """Использование диска"""
    total, used, free = shutil.disk_usage('/')
    pct = (used / total) * 100
    return {
        'total_gb': round(total / (1024**3), 1),
        'used_gb': round(used / (1024**3), 1),
        'free_gb': round(free / (1024**3), 1),
        'percent': round(pct, 1)
    }


def get_ram_usage():
    """Использование RAM"""
    try:
        with open('/proc/meminfo') as f:
            lines = f.readlines()
        info = {}
        for line in lines:
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip()
                val = int(parts[1].strip().split()[0])
                info[key] = val
        total = info.get('MemTotal', 0)
        available = info.get('MemAvailable', 0)
        used = total - available
        return {
            'total_mb': round(total / 1024),
            'used_mb': round(used / 1024),
            'available_mb': round(available / 1024),
            'percent': round((used / total) * 100, 1) if total else 0
        }
    except Exception:
        return {'error': 'cannot read'}


def get_uptime():
    """Аптайм сервера"""
    try:
        with open('/proc/uptime') as f:
            uptime_sec = float(f.read().split()[0])
        days = int(uptime_sec // 86400)
        hours = int((uptime_sec % 86400) // 3600)
        return f'{days}d {hours}h'
    except Exception:
        return 'unknown'


def full_health():
    """Полная проверка здоровья"""
    checks = {
        'openclaw_gateway': {
            'running': check_process('openclaw', 'openclaw-gatewa'),
            'port_18789': check_port(18789)
        },
        'trello_webhook': {
            'running': check_process('flask', 'trello-webhook-server'),
            'port_18790': check_port(18790)
        },
        'cloudflared': {
            'running': check_process('cloudflared', 'cloudflared tunnel')
        },
        'disk': get_disk_usage(),
        'ram': get_ram_usage(),
        'uptime': get_uptime(),
        'timestamp': datetime.now().isoformat()
    }

    # Определяем общий статус
    critical_ok = all([
        checks['openclaw_gateway']['running'],
        checks['openclaw_gateway']['port_18789'],
        checks['trello_webhook']['running'],
        checks['cloudflared']['running']
    ])

    disk_ok = checks['disk']['percent'] < 90
    ram_ok = checks['ram'].get('percent', 0) < 90

    if critical_ok and disk_ok and ram_ok:
        checks['status'] = 'healthy'
    elif critical_ok:
        checks['status'] = 'warning'
    else:
        checks['status'] = 'critical'

    return checks


class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health/ping':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'ok')
        elif self.path == '/health':
            health = full_health()
            status_code = 200 if health['status'] != 'critical' else 503
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(health, indent=2, ensure_ascii=False).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Тихий режим


if __name__ == '__main__':
    server = http.server.HTTPServer(('127.0.0.1', PORT), HealthHandler)
    print(f'🏥 AXIS Healthcheck running on http://127.0.0.1:{PORT}/health')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
