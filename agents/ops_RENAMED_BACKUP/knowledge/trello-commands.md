# ИНСТРУКЦИЯ ПО TRELLO ДЛЯ OPS COORDINATOR

Ты управляешь задачами студии через эти скрипты. Используй их через терминал (`exec`).

---

## 🔧 СКРИПТЫ И КОМАНДЫ

### 1. ПОЛУЧИТЬ СТАТУС ЗАДАЧ
**Скрипт:** `/home/axis/openclaw/trello-report.py`
**Команда:** `python3 /home/axis/openclaw/trello-report.py --status`
**Зачем:**
*   Узнать, сколько задач "В работе".
*   Проверить просроченные задачи (Expired).
*   Собрать статистику перед Планёркой.

### 2. СИНХРОНИЗИРОВАТЬ ДАННЫЕ
**Скрипт:** `/home/axis/openclaw/trello-sync.py`
**Команда:** `python3 /home/axis/openclaw/trello-sync.py`
**Зачем:**
*   Перед каждым отчетом.
*   Чтобы увидеть изменения, которые внесли люди руками.

### 3. СОБРАТЬ УТРЕННИЙ БРИФИНГ
**Скрипт:** `/home/axis/openclaw/trello-briefing.py`
**Команда:** `python3 /home/axis/openclaw/trello-briefing.py`
**Зачем:**
*   Получить сводку "Что сделано вчера / План на сегодня".
*   Публиковать в чат команды каждое утро в 09:00.

### 4. УПРАВЛЕНИЕ ДОСКАМИ
**Скрипт:** `/home/axis/openclaw/trello.py`
**Команды:**
*   `python3 /home/axis/openclaw/trello.py list` — список списков на доске.
*   `python3 /home/axis/openclaw/trello.py card create --name "Название" --desc "Описание"` — создать задачу.
*   `python3 /home/axis/openclaw/trello.py card move <CardID> <ListID>` — переместить задачу.

---

## 📋 ДОСКИ AXIS (ИЗ КОНФИГА)

У нас настроено 4 доски. Твоя основная — **Производство**.

### 1. Производство (Основная)
**ID:** `697ea1c3b95f7266bd54f96b`
**Списки:**
*   `inProgress` (В работе)
*   `backlog` (Очередь)
*   `today` (Сегодня)
*   `done` (Готово)

### 2. Стратегия (Квартальные цели)
**ID:** `6981a0e378e59c2466b8ab87`
**Списки:** `цели_квартала`, `этот_месяц`, `внедряю`.

### 3. СЭД Авторский надзор
**ID:** `69896df8e0a9c116e288f93d`
**Списки:** `inProgress`, `onPayment` (На оплате), `onInstallation` (На монтаже).

### 4. C3 — Рабочий проект
**ID:** `698c54cb7e2d0c110ddfdd50`
**Списки:** `inProgress`, `review` (На проверку), `corrections` (Правки).
