# TOOLS.md - Local Notes

## Социальные сети
- **Telegram канал:** [ссылка]
- **Instagram:** [ссылка]
- **Facebook:** [ссылка]
- **TikTok:** [ссылка]
- **LinkedIn:** [ссылка]
- **YouTube:** [ссылка]

## Контент
- **Notion:** [ссылка на контент-план]
- **Figma:** [ссылка на шаблоны]
- **Canva:** [ссылка на дизайны]


## 🧠 Поиск по базе знаний (Semantic Search)

### Поиск по прошлым проектам и памяти
```bash
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос"
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --top 10
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --grep  # fallback без OpenAI
```
База: ChromaDB (381+ документов — прошлые проекты, память агентов).
Используй при получении новых задач для поиска похожих прошлых проектов.

