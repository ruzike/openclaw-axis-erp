# TOOLS.md - AXIS Coach

## 📁 Google Drive — AXIS Coach Videos

**Аккаунт:** ruslanshakirzhanovich@gmail.com
**Папка:** AXIS Coach Videos
**Folder ID:** 17ug1nv7WN8S3_ucE68yv2TObcBUa4GtB
**Ссылка:** https://drive.google.com/drive/folders/17ug1nv7WN8S3_ucE68yv2TObcBUa4GtB

### Загрузка файла на Drive:
```bash
python3 /home/axis/openclaw/agents/coach/gdrive-upload.py /path/to/file.mp4
# Возвращает публичную ссылку на файл
```

### Токены: /home/axis/.config/gogcli/token-ruslanshakirzhanovich.json
### Credentials: /home/axis/.config/gogcli/credentials.json

## Cron напоминания
Используй OpenClaw cron для ежедневных check-in привычек.

## Делегирование
Используй `sessions_send` для передачи задач другим агентам.

## Скрипт загрузки видео (gdrive-upload.py)

Скрипт `gdrive-upload.py` предназначен для автоматической загрузки видеофайлов (и текстовых файлов) в папку `AXIS Coach Videos` на Google Drive и получения публичной ссылки.

### Как запускать скрипт:
```bash
python3 /home/axis/openclaw/agents/coach/gdrive-upload.py /path/to/video.mp4
```
*Поддерживаемые форматы:* `.mp4`, `.mov`, `.avi`, `.mkv`, `.txt`, `.md`.

### ID папки "AXIS Coach Videos":
Папка создается автоматически при первой успешной загрузке файла.
*ID папки:* **Будет выведен в консоль при первом запуске (необходимо обновить этот файл после первого запуска)**.
*Название папки:* `AXIS Coach Videos`

### Какой Google-аккаунт используется:
Используйте аккаунт **`axis.intelekt@gmail.com`** (или другой рабочий `design3d.kz@gmail.com` / `archvizbusiness@gmail.com`). 

> **Важно по авторизации (OAuth 2.0):** 
> Системные токены OpenClaw (google-antigravity) по умолчанию не имеют прав на Google Drive (ограничение scopes). Поэтому для работы скрипта требуется единоразовая настройка:
> 1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/), включите **Google Drive API**.
> 2. Создайте учетные данные **OAuth 2.0 Client IDs** (Тип: Desktop App).
> 3. Скачайте JSON-файл и сохраните его как `~/.openclaw/credentials/coach-client-secret.json`.
> 4. При первом запуске скрипта в консоли появится ссылка. Перейдите по ней в браузере, авторизуйтесь под аккаунтом `axis.intelekt@gmail.com` и дайте разрешение. Токен будет сохранен в `~/.openclaw/credentials/coach-gdrive-token.json` и больше не потребует ручного вмешательства.


## 🧠 Поиск по базе знаний (Semantic Search)

### Поиск по прошлым проектам и памяти
```bash
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос"
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --top 10
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос" --grep  # fallback без OpenAI
```
База: ChromaDB (381+ документов — прошлые проекты, память агентов).
Используй при получении новых задач для поиска похожих прошлых проектов.

