#!/usr/bin/env python3
"""
AXIS KPI Checker — автоматический подсчёт дисциплины сотрудников
Запуск: python3 kpi-trello-check.py [--week]
Выход: JSON + текстовый отчёт для Telegram
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

# Config
TZ = timezone(timedelta(hours=5))
NOW = datetime.now(TZ)
TRELLO_KEY = os.environ.get("TRELLO_API_KEY", "")
TRELLO_TOKEN = os.environ.get("TRELLO_TOKEN", "")

# Load from axis config if env not set
if not TRELLO_KEY:
    config_path = Path("/home/axis/openclaw/axis-system/trello-config.json")
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)
            TRELLO_KEY = cfg.get("api_key", "")
            TRELLO_TOKEN = cfg.get("token", "")

TRELLO_BASE = "https://api.trello.com/1"

# Team members - Trello member IDs need to be mapped
TEAM = {
    "Мирас": {"telegram_id": "MEMBER1_TELEGRAM_ID", "trello_username": None},
    "Бахытжан": {"telegram_id": "MEMBER2_TELEGRAM_ID", "trello_username": None},
}

STATE_FILE = Path("/home/axis/openclaw/axis-system/axis-state.json")
KPI_LOG = Path("/home/axis/openclaw/axis-system/kpi-log.json")


def load_trello_cards():
    """Load cards from axis-state.json"""
    if not STATE_FILE.exists():
        return []
    with open(STATE_FILE) as f:
        data = json.load(f)
    cards = []
    prod = data.get("trello", {}).get("production", {})
    for lst, items in prod.items():
        for card in items:
            due = card.get("due")
            overdue = False
            stale = False
            if due:
                try:
                    due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
                    if due_dt < NOW:
                        overdue = True
                except:
                    pass
            
            # Check staleness (no update >48h)
            last_activity = card.get("dateLastActivity")
            if last_activity and lst == "В работе":
                try:
                    la_dt = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
                    hours_since = (NOW - la_dt).total_seconds() / 3600
                    if hours_since > 48:
                        stale = True
                except:
                    pass
            
            cards.append({
                "name": card["name"],
                "list": lst,
                "due": due,
                "overdue": overdue,
                "stale": stale,
                "members": card.get("idMembers", []),
            })
    return cards


def check_trello_discipline(cards):
    """Check Trello update discipline"""
    in_work = [c for c in cards if c["list"] == "В работе"]
    stale = [c for c in in_work if c["stale"]]
    overdue = [c for c in cards if c["overdue"]]
    
    return {
        "total_in_work": len(in_work),
        "stale_cards": len(stale),
        "stale_names": [c["name"][:40] for c in stale],
        "overdue_count": len(overdue),
        "overdue_names": [c["name"][:40] for c in overdue],
        "score": max(0, 100 - (len(stale) * 20) - (len(overdue) * 10)),
    }


def check_briefing():
    """Check Google Form briefing responses for today"""
    import subprocess
    try:
        env = os.environ.copy()
        env["GOOGLE_FORMS_CREDENTIALS"] = "/home/axis/.openclaw/credentials/google-forms-oauth.json"
        result = subprocess.run(
            ["node", "/home/axis/openclaw/skills/google-forms/google-forms.js",
             "responses", "--form-id", "1MxSLsEkMK12OBiSh9GPWrl3sf0ou4w4ksps4HhO3jbc", "--json"],
            capture_output=True, text=True, timeout=30, env=env,
            cwd="/home/axis/openclaw/skills/google-forms"
        )
        if result.returncode != 0:
            return {"score": None, "note": f"Ошибка Forms API: {result.stderr[:100]}"}
        
        data = json.loads(result.stdout)
        today = NOW.strftime("%Y-%m-%d")
        
        expected = {"Руслан", "Мирас", "Бахытжан"}
        filled = set()
        
        for resp in data.get("responses", []):
            resp_date = resp.get("lastSubmittedTime", "")[:10]
            if resp_date == today:
                for ans in resp.get("answers", {}).values():
                    texts = ans.get("textAnswers", {}).get("answers", [])
                    for t in texts:
                        if t.get("value") in expected:
                            filled.add(t["value"])
        
        missing = expected - filled
        score = round(len(filled) / len(expected) * 100)
        
        return {
            "score": score,
            "filled": sorted(filled),
            "missing": sorted(missing),
            "note": f"Заполнили: {', '.join(sorted(filled)) or 'никто'}" + 
                    (f" | Не заполнили: {', '.join(sorted(missing))}" if missing else ""),
        }
    except Exception as e:
        return {"score": None, "note": f"Ошибка: {str(e)[:100]}"}


def check_plan_report():
    """Check Google Sheets plan report for this week"""
    import subprocess, urllib.request
    try:
        token_file = "/home/axis/.config/gogcli/token-ruslanshakirzhanovich.json"
        creds_file = "/home/axis/.config/gogcli/credentials.json"
        
        with open(token_file) as f:
            token_data = json.load(f)
        with open(creds_file) as f:
            creds = json.load(f)
        
        # Refresh token
        data = urllib.parse.urlencode({
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": token_data["refresh_token"],
            "grant_type": "refresh_token",
        }).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
        resp = urllib.request.urlopen(req, timeout=10)
        new_token = json.loads(resp.read())
        access_token = new_token["access_token"]
        
        # Read sheet
        sheet_id = "13Hg_hwq28PmmkfgPiPsid-7Np5xzlk0HFDVB-yTlFJ8"
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/A1:Z50"
        req2 = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
        resp2 = urllib.request.urlopen(req2, timeout=10)
        sheet_data = json.loads(resp2.read())
        rows = sheet_data.get("values", [])
        
        # Check if anyone filled data (non-header rows with content)
        data_rows = [r for r in rows[4:] if any(cell.strip() for cell in r if cell.strip())]
        
        if data_rows:
            return {"score": 100, "note": f"Таблица заполнена ({len(data_rows)} строк с данными)"}
        else:
            return {"score": 0, "note": "Таблица пустая — никто не заполнил план-отчёт"}
    except Exception as e:
        return {"score": None, "note": f"Ошибка: {str(e)[:100]}"}


def calculate_kpi():
    """Calculate overall KPI"""
    cards = load_trello_cards()
    trello = check_trello_discipline(cards)
    briefing = check_briefing()
    plan_report = check_plan_report()
    
    kpi = {
        "date": NOW.strftime("%Y-%m-%d"),
        "trello": {
            "score": trello["score"],
            "stale_cards": trello["stale_cards"],
            "overdue": trello["overdue_count"],
            "details": trello,
        },
        "briefing": briefing,
        "plan_report": plan_report,
        "overall": {
            "trello_weight": 0.33,
            "briefing_weight": 0.33,
            "plan_report_weight": 0.34,
        },
    }
    
    # Calculate overall score from available metrics
    available_scores = []
    for key in ["trello", "briefing", "plan_report"]:
        s = kpi[key].get("score")
        if s is not None:
            available_scores.append(s)
    
    kpi["overall"]["available_score"] = round(sum(available_scores) / len(available_scores)) if available_scores else 0
    kpi["overall"]["data_completeness"] = f"{len(available_scores)}/3 метрик"
    
    return kpi


def format_report(kpi):
    """Format KPI report for Telegram"""
    trello = kpi["trello"]["details"]
    
    report = f"""📊 KPI ДИСЦИПЛИНЫ — {kpi['date']}

🔹 **Trello** (что можем измерить сейчас):
  В работе: {trello['total_in_work']} карточек
  Зависших (>48ч): {trello['stale_cards']} {'🔴' if trello['stale_cards'] > 0 else '🟢'}
  Просрочено: {trello['overdue_count']} {'🔴' if trello['overdue_count'] > 0 else '🟢'}
  Балл: {trello['score']}%"""
    
    if trello["stale_names"]:
        report += "\n\n  ⚠️ Зависшие:"
        for name in trello["stale_names"][:5]:
            report += f"\n  • {name}"
    
    if trello["overdue_names"]:
        report += "\n\n  🔴 Просроченные:"
        for name in trello["overdue_names"][:5]:
            report += f"\n  • {name}"
    
    briefing = kpi["briefing"]
    b_score = briefing.get("score")
    b_icon = "🟢" if b_score and b_score == 100 else "🟡" if b_score and b_score > 0 else "🔴"
    
    plan = kpi["plan_report"]
    p_score = plan.get("score")
    p_icon = "🟢" if p_score and p_score == 100 else "🟡" if p_score and p_score > 0 else "🔴"
    
    report += f"""

🔹 **Утренний брифинг:** {b_icon} {briefing['note']}
🔹 **План-отчёт:** {p_icon} {plan['note']}

📈 **Общий балл:** {kpi['overall']['available_score']}% ({kpi['overall']['data_completeness']})"""
    
    return report


def save_log(kpi):
    """Append KPI to log file"""
    log = []
    if KPI_LOG.exists():
        try:
            with open(KPI_LOG) as f:
                log = json.load(f)
        except:
            log = []
    
    log.append(kpi)
    
    # Keep last 90 days
    log = log[-90:]
    
    with open(KPI_LOG, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def main():
    kpi = calculate_kpi()
    save_log(kpi)
    
    if "--json" in sys.argv:
        print(json.dumps(kpi, ensure_ascii=False, indent=2))
    else:
        print(format_report(kpi))


if __name__ == "__main__":
    main()
