# TOOLS.md - Finance Agent

## 📊 Google Sheets (через GOG CLI)

**Чтение таблиц:**
```bash
export PATH=$PATH:/home/axis/bin/go/bin:/home/axis/go/bin
export GOG_KEYRING_PASSWORD="axis2026"
gog sheets read "SPREADSHEET_ID" "Лист1!A1:Z100" --account ruslanshakirzhanovich@gmail.com
```

**Основная таблица:**
- Название: "AXIS — Форма план-отчёта"
- ID: (проверить через `gog sheets list`)

**Важно:** Не использовать прямой API — токен протух. Только через GOG CLI.

---

## 💰 Финансовые данные

**Счета:**
- CED GROUP (основной клиент)
- Дебиторка: проверять еженедельно

**Cash Flow:**
- Еженедельный отчёт — пятница 17:00
- Прогноз на 4 недели вперёд

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


## 📊 Google Sheets (GOG CLI)

### Чтение таблицы
```bash
export PATH=$PATH:/home/axis/bin/go/bin:/home/axis/go/bin
export GOG_KEYRING_PASSWORD="axis2026"
gog sheets read "SPREADSHEET_ID" "Лист1!A1:Z100" --account ruslanshakirzhanovich@gmail.com
```

### Метаданные (узнать имена листов)
```bash
gog sheets metadata "SPREADSHEET_ID" --account ruslanshakirzhanovich@gmail.com --json
```

### Запись в таблицу
```bash
gog sheets update "SPREADSHEET_ID" "Лист1!A1:B2" --values-json '[["A","B"],["1","2"]]' --input USER_ENTERED --account ruslanshakirzhanovich@gmail.com
```

НЕ используй прямые OAuth токены — используй GOG CLI (токен в keyring, обновляется автоматически).
