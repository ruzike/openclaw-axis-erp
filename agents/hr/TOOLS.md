# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.


## 🧠 Поиск по базе знаний (Semantic Search)

### Поиск по прошлым проектам и памяти
```bash
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос"
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --top 10
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --grep  # fallback без OpenAI
```
База: ChromaDB (381+ документов — прошлые проекты, память агентов).
Используй при получении новых задач для поиска похожих прошлых проектов.

