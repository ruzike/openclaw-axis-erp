#!/usr/bin/env python3
"""
Claude API Limits Checker
Проверяет лимиты Anthropic API и выводит в формате прогресс-баров.
Usage: python3 claude-limits.py [--json]
"""

import json
import sys
import os
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("❌ pip install requests")
    sys.exit(1)

# --- Конфиг ---
CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")

MODELS_TO_CHECK = [
    ("claude-opus-4-6", "Opus 4.6"),
    ("claude-sonnet-4-5-20250929", "Sonnet 4.5"),
    ("claude-3-haiku-20240307", "Haiku 3"),
]

def load_api_key():
    with open(CONFIG_PATH) as f:
        c = json.load(f)
    return c["env"]["ANTHROPIC_API_KEY"]

def check_model_limits(api_key, model_id):
    """Делает минимальный запрос к модели и считывает rate-limit headers."""
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model_id,
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "."}],
            },
            timeout=20,
        )
    except Exception as e:
        return {"error": str(e)}

    if r.status_code == 529:
        return {"error": "API overloaded (529)"}
    if r.status_code not in (200, 429):
        return {"error": f"HTTP {r.status_code}: {r.text[:100]}"}

    h = r.headers
    result = {}

    # Requests
    req_limit = int(h.get("anthropic-ratelimit-requests-limit", 0))
    req_remaining = int(h.get("anthropic-ratelimit-requests-remaining", 0))
    req_reset = h.get("anthropic-ratelimit-requests-reset", "")
    if req_limit:
        result["requests"] = {
            "limit": req_limit,
            "remaining": req_remaining,
            "used": req_limit - req_remaining,
            "pct": round((req_limit - req_remaining) / req_limit * 100),
            "reset": req_reset,
        }

    # Input tokens
    in_limit = int(h.get("anthropic-ratelimit-input-tokens-limit", 0))
    in_remaining = int(h.get("anthropic-ratelimit-input-tokens-remaining", 0))
    in_reset = h.get("anthropic-ratelimit-input-tokens-reset", "")
    if in_limit:
        result["input_tokens"] = {
            "limit": in_limit,
            "remaining": in_remaining,
            "used": in_limit - in_remaining,
            "pct": round((in_limit - in_remaining) / in_limit * 100),
            "reset": in_reset,
        }

    # Output tokens
    out_limit = int(h.get("anthropic-ratelimit-output-tokens-limit", 0))
    out_remaining = int(h.get("anthropic-ratelimit-output-tokens-remaining", 0))
    out_reset = h.get("anthropic-ratelimit-output-tokens-reset", "")
    if out_limit:
        result["output_tokens"] = {
            "limit": out_limit,
            "remaining": out_remaining,
            "used": out_limit - out_remaining,
            "pct": round((out_limit - out_remaining) / out_limit * 100),
            "reset": out_reset,
        }

    # Total tokens
    tok_limit = int(h.get("anthropic-ratelimit-tokens-limit", 0))
    tok_remaining = int(h.get("anthropic-ratelimit-tokens-remaining", 0))
    tok_reset = h.get("anthropic-ratelimit-tokens-reset", "")
    if tok_limit:
        result["total_tokens"] = {
            "limit": tok_limit,
            "remaining": tok_remaining,
            "used": tok_limit - tok_remaining,
            "pct": round((tok_limit - tok_remaining) / tok_limit * 100),
            "reset": tok_reset,
        }

    # Rate limited?
    result["rate_limited"] = r.status_code == 429
    return result

def progress_bar(pct, width=12):
    filled = round(width * pct / 100)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    return bar

def format_reset(reset_str):
    if not reset_str:
        return ""
    try:
        reset_dt = datetime.fromisoformat(reset_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = reset_dt - now
        secs = int(diff.total_seconds())
        if secs <= 0:
            return "сейчас"
        if secs < 60:
            return f"{secs}сек"
        mins = secs // 60
        if mins < 60:
            return f"{mins}мин"
        hours = mins // 60
        mins_left = mins % 60
        return f"{hours}ч {mins_left}мин"
    except:
        return reset_str[:16]

def status_emoji(pct):
    if pct >= 90:
        return "🔴"
    if pct >= 70:
        return "⚠️"
    return "✅"

def format_number(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)

def main():
    json_mode = "--json" in sys.argv
    api_key = load_api_key()

    all_results = {}
    output_lines = ["🤖 **Anthropic API Limits**", ""]

    for model_id, model_name in MODELS_TO_CHECK:
        data = check_model_limits(api_key, model_id)
        all_results[model_id] = data

        if "error" in data:
            output_lines.append(f"**{model_name}:** ❌ {data['error']}")
            output_lines.append("")
            continue

        # Requests
        if "requests" in data:
            r = data["requests"]
            bar = progress_bar(r["pct"])
            reset = format_reset(r["reset"])
            emoji = status_emoji(r["pct"])
            output_lines.append(f"**{model_name}** — Requests (сброс: {reset})")
            output_lines.append(f"{bar} {r['pct']}% ({r['used']}/{r['limit']}) {emoji}")

        # Total tokens
        if "total_tokens" in data:
            t = data["total_tokens"]
            bar = progress_bar(t["pct"])
            reset = format_reset(t["reset"])
            emoji = status_emoji(t["pct"])
            output_lines.append(f"Tokens: {bar} {t['pct']}% ({format_number(t['used'])}/{format_number(t['limit'])}) {emoji}")

        if data.get("rate_limited"):
            output_lines.append("🔴 RATE LIMITED!")

        output_lines.append("")

    # Overall status
    max_pct = 0
    for d in all_results.values():
        if "error" not in d:
            for k in ("requests", "input_tokens", "output_tokens", "total_tokens"):
                if k in d:
                    max_pct = max(max_pct, d[k]["pct"])

    if max_pct >= 90:
        output_lines.append("🔴 Лимиты почти исчерпаны!")
    elif max_pct >= 70:
        output_lines.append("⚠️ Лимиты выше 70%, осторожнее")
    else:
        output_lines.append("✅ Всё ок, запас есть")

    if json_mode:
        print(json.dumps(all_results, indent=2, ensure_ascii=False))
    else:
        print("\n".join(output_lines))

if __name__ == "__main__":
    main()
