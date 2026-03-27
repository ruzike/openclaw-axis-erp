#!/usr/bin/env python3
"""
Pomodoro 50/10 Timer
--------------------
Этот скрипт запускает таймер Pomodoro в фоновом режиме (daemon) и использует openclaw для отправки уведомлений в Telegram.

ВАЖНО: При запуске через cron или в фоновом демоне (после os.fork) теряется переменная PATH, 
из-за чего система не может найти nvm, node и openclaw.
Для решения этой проблемы в функции send_message используются:
1. Абсолютные пути к исполняемому файлу node и скрипту openclaw.
2. Явное добавление пути к node в переменную окружения PATH перед вызовом subprocess.
"""
import time
import subprocess
import sys
import argparse
import os

def send_message(user_id, text):
    # Используем системный openclaw (/usr/bin/openclaw) — не зависит от nvm
    subprocess.run([
        "/usr/bin/openclaw", "message", "send",
        "--channel", "telegram",
        "--account", "ops",
        "--target", str(user_id),
        "--message", text
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    parser = argparse.ArgumentParser(description="Pomodoro 50/10 Timer")
    parser.add_argument("user_id", help="Telegram User ID")
    parser.add_argument("task", help="Task name")
    parser.add_argument("--cycles", type=int, default=1, help="Number of 50/10 cycles")
    parser.add_argument("--daemon", action="store_true", help="Run in background")
    args = parser.parse_args()

    if args.daemon:
        print(f"✅ Таймер (daemon) запущен. Циклов: {args.cycles}, Задача: {args.task}.")
        if os.fork() > 0: sys.exit()
        os.setsid()
        if os.fork() > 0: sys.exit()
        with open('/dev/null', 'r') as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open('/tmp/pomodoro.log', 'a') as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
            os.dup2(f.fileno(), sys.stderr.fileno())

    send_message(args.user_id, f"⚡️ БЛОК. Задача: {args.task}. 50 минут. Старт. 🚀")

    for i in range(args.cycles):
        time.sleep(25 * 60)
        # Молчаливый чек 25 минут - пропускаем (не мешаем)
        
        time.sleep(25 * 60)
        send_message(args.user_id, f"🛑 СТОП. Блок {i+1} из {args.cycles} завершён. Какой результат по: {args.task}? Отчитывайся. 10 минут отдых.")
        
        if i < args.cycles - 1:
            time.sleep(10 * 60)
            send_message(args.user_id, f"🚀 Конец перерыва! Погнали в следующий блок. Задача: {args.task}. Фокус 50 минут!")

if __name__ == "__main__":
    main()
