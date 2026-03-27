# Семантический поиск по projects-history

Система семантического поиска на базе ChromaDB и OpenAI Embeddings.  
Находит документы по **смыслу**, а не только по точному совпадению слов.

## Быстрый старт

```bash
# 1. Индексация (первый запуск или после добавления файлов)
python3 /home/axis/openclaw/axis-system/semantic-index.py

# 2. Поиск
python3 /home/axis/openclaw/axis-system/semantic-search.py "ваш запрос"
```

## Скрипты

### semantic-index.py — Индексация

```bash
# Инкрементальная индексация (только новые/изменённые файлы)
python3 semantic-index.py

# Полная переиндексация (с нуля)
python3 semantic-index.py --rebuild

# Проверить статус базы
python3 semantic-index.py --check
```

**Что делает:**
- Сканирует `/home/axis/openclaw/projects-history/**/*.md`
- Генерирует embeddings через OpenAI API (`text-embedding-ada-002`)
- Сохраняет в ChromaDB (`.chroma-db/`)
- Отслеживает изменения по MD5 хешу файлов

### semantic-search.py — Поиск

```bash
# Базовый поиск (топ-5)
python3 semantic-search.py "запрос"

# Больше результатов
python3 semantic-search.py "запрос" --top 10

# С отладкой
python3 semantic-search.py "запрос" --verbose

# Fallback на grep (если индекс недоступен)
python3 semantic-search.py "запрос" --grep
```

## Примеры семантического поиска

| Запрос | Что найдёт | Почему |
|--------|------------|--------|
| `кафе` | Ресторан "Восток" | Семантическая связь: кафе ≈ ресторан |
| `видеоролик` | ТРЦ Mega Silk Way (анимация) | видеоролик ≈ анимация ≈ ролик |
| `жильё` | ЖК Almaty Towers, Вилла | жильё ≈ квартира ≈ дом ≈ вилла |
| `смета` | Проекты с бюджетами | смета ≈ расчёт ≈ бюджет ≈ оценка |
| `проблемы с клиентом` | Проекты со сложностями | Ищет по смыслу "проблема" |

## Технические детали

### Архитектура

```
projects-history/*.md
         ↓
    [Chunking]         — разбивка на фрагменты 1500 символов
         ↓
 [OpenAI Embeddings]   — text-embedding-ada-002 (1536 dim)
         ↓
    [ChromaDB]         — векторная база данных
         ↓
  [Similarity Search]  — косинусное сходство
```

### Конфигурация

| Параметр | Значение | Где изменить |
|----------|----------|--------------|
| Директория проектов | `/home/axis/openclaw/projects-history` | `HISTORY_DIR` |
| База ChromaDB | `/home/axis/openclaw/axis-system/.chroma-db` | `CHROMA_DIR` |
| Модель embeddings | `text-embedding-ada-002` | `EMBEDDING_MODEL` |
| Размер чанка | 1500 символов | `CHUNK_SIZE` |
| Минимальная релевантность | 30% | `MIN_SIMILARITY` |

### Требования

```bash
pip install chromadb openai
export OPENAI_API_KEY="sk-..."  # или в .env
```

## Интеграция с агентами

В `TOOLS.md` агентов добавить:

```markdown
### Семантический поиск по истории проектов
```bash
python3 /home/axis/openclaw/axis-system/semantic-search.py "запрос"
```
```

## Обслуживание

### Автоматическая индексация (cron)

```bash
# Каждый час
0 * * * * python3 /home/axis/openclaw/axis-system/semantic-index.py >> /var/log/semantic-index.log 2>&1
```

### Полная переиндексация

Рекомендуется после:
- Изменения модели embeddings
- Изменения размера чанков
- Серьёзных ошибок в базе

```bash
python3 semantic-index.py --rebuild
```

## Отладка

### Индекс не найден
```
❌ Семантический индекс не найден.
```
**Решение:** Запустите `python3 semantic-index.py`

### Пустые результаты
**Причины:**
1. Индекс пуст — добавьте файлы и переиндексируйте
2. Запрос слишком специфичный — попробуйте более общие термины
3. Порог релевантности — используйте `--grep` для fallback

### Проверка статуса
```bash
python3 semantic-index.py --check
```

## Тестовые результаты (2026-03-02)

Запрос: **"кафе"** (нет такого слова в документах)
```
1. Ресторан "Восток" — 77% ✓ (семантическая связь)
```

Запрос: **"видеоролик рекламный"**
```
1. ТРЦ "Mega Silk Way" - Рекламная анимация — 81% ✓
```

Запрос: **"жильё квартира"**
```
1. Частная вилла на Боровом — 79% ✓
2. ЖК "Almaty Towers" — 79% ✓
```

Запрос: **"смета расчёт стоимости"**
```
1. ЖК "Almaty Towers" — 80% ✓ (содержит раздел "Оценка стоимости")
```

---

**Автор:** DevOps Agent  
**Дата:** 2026-03-02  
**Версия:** 1.0
