#!/usr/bin/env python3
"""Мониторинг системы AXIS

Проверяет:
1. Логи cron задач
2. Ошибки в логах
3. Статус Trello интеграций
4. Состояние сотрудников

Ошибки → эскалация Руслану
"""
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

# Конфигурация
LOG_DIR = Path('/tmp')
STATE_FILE = Path('/home/axis/openclaw/axis-system/monitor-state.json')
ESCALATION_FILE = Path('/home/axis/openclaw/axis-system/escalations.json')

def load_state():
    """Загрузить состояние мониторинга"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_checks': {},
        'errors': [],
        'warnings': []
    }

def save_state(state):
    """Сохранить состояние"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def check_logs():
    """Проверить логи cron задач"""
    errors = []
    warnings = []

    # Проверяем только логи других сервисов (НЕ свой monitor.log — иначе снежный ком)
    log_files = ['ingress.log', 'trello-butler.log', 'semantic-index.log']

    for log_file in log_files:
        log_path = LOG_DIR / log_file
        if not log_path.exists():
            warnings.append(f"Лог {log_file} не создан")
            continue

        # Проверить последние 50 строк на ошибки
        try:
            result = subprocess.run(
                ['tail', '-50', str(log_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                errors.append(f"Ошибка чтения {log_file}")

            lines = result.stdout.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Обнаружить ошибки
                if '❌' in line or 'ERROR' in line or 'Exception' in line:
                    errors.append(f"{log_file}: {line[:100]}")

                # Обнаружить предупреждения
                if '⚠️' in line or 'WARNING' in line:
                    warnings.append(f"{log_file}: {line[:100]}")

        except Exception as e:
            errors.append(f"Ошибка проверки {log_file}: {e}")

    return errors, warnings

def check_trello():
    """Проверить интеграцию с Trello"""
    errors = []
    warnings = []

    try:
        # Проверить конфиг
        config_path = Path('/home/axis/openclaw/trello-config.json')
        if not config_path.exists():
            errors.append("trello-config.json не найден")
            return errors, warnings

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Проверить API ключи
        if not config.get('api', {}).get('key'):
            errors.append("trello-config.json: API key не указан")

        if not config.get('api', {}).get('token'):
            errors.append("trello-config.json: API token не указан")

        # Проверить доску C3
        if not config.get('boards', {}).get('c3'):
            warnings.append("trello-config.json: доска C3 не настроена")
        else:
            c3_board = config['boards']['c3']
            if not c3_board.get('id'):
                errors.append("trello-config.json: ID доски C3 не указан")

            # Проверить списки
            lists = c3_board.get('lists', {})
            required_lists = ['backlog', 'inProgress', 'review', 'done']
            for list_name in required_lists:
                if not lists.get(list_name, {}).get('id'):
                    warnings.append(f"trello-config.json: список {list_name} не настроен")

    except json.JSONDecodeError:
        errors.append("trello-config.json: некорректный JSON")
    except Exception as e:
        errors.append(f"Ошибка проверки Trello: {e}")

    return errors, warnings

def check_employees():
    """Проверить состояние сотрудников"""
    errors = []
    warnings = []

    state_path = Path('/home/axis/openclaw/team-state.json')
    if not state_path.exists():
        errors.append("team-state.json не найден")
        return errors, warnings

    try:
        with open(state_path, 'r') as f:
            state = json.load(f)

        employees = state.get('employees', {})
        for emp_id, emp_data in employees.items():
            # Проверить активность за последние 24 часа
            last_checkin = emp_data.get('last_checkin')
            if last_checkin:
                last_checkin_dt = datetime.fromisoformat(last_checkin)
                hours_ago = (datetime.now() - last_checkin_dt).total_seconds() / 3600
                if hours_ago > 24:
                    warnings.append(f"{emp_data.get('name', emp_id)}: неактивен более 24ч")

    except Exception as e:
        errors.append(f"Ошибка проверки сотрудников: {e}")

    return errors, warnings

def check_cron():
    """Проверить cron задачи"""
    errors = []
    warnings = []

    try:
        result = subprocess.run(
            ['crontab', '-l'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            errors.append("Ошибка чтения crontab")
            return errors, warnings

        # Проверить наличие cron задач
        required_jobs = ['monitor.py', 'semantic-index.py', 'trello-automation.py']
        for job in required_jobs:
            if job not in result.stdout:
                warnings.append(f"Cron задача {job} не найдена")

    except Exception as e:
        errors.append(f"Ошибка проверки cron: {e}")

    return errors, warnings

def generate_report(errors, warnings):
    """Сгенерировать отчёт"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    report = f"""
{'='*70}
📊 МОНИТОРИНГ СИСТЕМЫ AXIS
{'='*70}
Время: {now}

🚨 ОШИБКИ ({len(errors)}):
"""

    if errors:
        for i, error in enumerate(errors, 1):
            report += f"\n{i}. {error}"
    else:
        report += "\nНет критических ошибок"

    report += f"\n\n⚠️ ПРЕДУПРЕЖДЕНИЯ ({len(warnings)}):"

    if warnings:
        for i, warning in enumerate(warnings, 1):
            report += f"\n{i}. {warning}"
    else:
        report += "\nНет предупреждений"

    report += f"\n\n{'='*70}"

    return report

def main():
    """Главная функция"""
    print("🔍 Проверка системы AXIS...")

    # Загрузить состояние
    state = load_state()

    # Проверить все компоненты
    errors, warnings = [], []

    log_errors, log_warnings = check_logs()
    errors.extend(log_errors)
    warnings.extend(log_warnings)

    trello_errors, trello_warnings = check_trello()
    errors.extend(trello_errors)
    warnings.extend(trello_warnings)

    emp_errors, emp_warnings = check_employees()
    errors.extend(emp_errors)
    warnings.extend(emp_warnings)

    cron_errors, cron_warnings = check_cron()
    errors.extend(cron_errors)
    warnings.extend(cron_warnings)

    # Обновить состояние
    state['last_checks'] = {
        'timestamp': datetime.now().isoformat(),
        'errors_count': len(errors),
        'warnings_count': len(warnings)
    }
    save_state(state)

    # Сгенерировать отчёт
    report = generate_report(errors, warnings)

    print(report)

    # Эскалация при ошибках
    if errors:
        print(f"\n🚨 Обнаружены {len(errors)} ошибки! Требуется внимание Руслана.")
        print(f"Отчёт сохранён в {STATE_FILE}")

        # Записать эскалацию
        if ESCALATION_FILE.exists():
            with open(ESCALATION_FILE, 'r') as f:
                escalations = json.load(f)
        else:
            escalations = []

        escalation = {
            'timestamp': datetime.now().isoformat(),
            'type': 'monitoring_error',
            'errors': errors
        }
        escalations.append(escalation)

        with open(ESCALATION_FILE, 'w') as f:
            json.dump(escalations, f, indent=2, ensure_ascii=False)

        return 1  # Код ошибки

    return 0

if __name__ == '__main__':
    sys.exit(main())
