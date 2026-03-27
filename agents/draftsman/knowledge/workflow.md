# Рабочий процесс и публикация

## Шаги работы

### 1. Сбор фактуры
Для постов об AI-системе — запрашивай через `sessions_spawn`:
- `agentId: "tech"` — регламенты, внедрения, документы
- `agentId: "devops"` — инфраструктура, сбои, оптимизации
- `agentId: "ops"` — ритуалы, координация команды

### 2. Создание поста
1. Определи рубрику и формат (из content-strategy.md)
2. Напиши пост по шаблону
3. Сгенерируй картинку

### 3. Генерация картинки
**Скрипт:** `/home/axis/openclaw/skills/seedream/generate_image.py`
```bash
python3 /home/axis/openclaw/skills/seedream/generate_image.py "промпт EN" --out "/home/axis/openclaw/agents/shket/название.jpg"
```

**Стили по рубрикам:**
- Инструменты: `clean minimalist business infographic, dark background, glowing blue elements, professional`
- Кейсы: `business growth chart, upward arrow, dark theme, data dashboard, cinematic lighting`
- AI/Build in Public: `cyberpunk AI visualization, neon lights, neural network, glitch art, dark, 8k`
- Мышление: `thought-provoking abstract business, minimalist, dark premium, single visual metaphor`

Если скрипт ошибка — публикуй без картинки с эмодзи. HF_TOKEN уже в конфиге.

### 4. Согласование (ОБЯЗАТЕЛЬНО!)
```bash
python3 /home/axis/openclaw/agents/shket/post_to_telegram.py YOUR_TELEGRAM_ID /home/axis/openclaw/agents/shket/[картинка].png "📝 Пост на согласование:\n[Текст]"
```
Жди: "Одобрено" → публикуй. "Исправить" → правь → снова согласование.

### 5. Публикация
```bash
python3 /home/axis/openclaw/agents/shket/post_to_telegram.py "@neuro_dir" /home/axis/openclaw/agents/shket/[картинка].png "[Текст]"
```
