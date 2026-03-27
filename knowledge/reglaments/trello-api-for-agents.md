# TRELLO API ДЛЯ АГЕНТОВ
# Регламент автономной работы с Trello
# Версия: 1.0 | Дата: 2026-02-17 | Статус: ✅ Проверено

---

## 🎯 ЦКП (Ценный Конечный Продукт)
Агент может создать, прочитать, переместить и обновить карточку в Trello **без участия Руслана**.

---

## 🔑 КОНФИГУРАЦИЯ

**Файл конфига:** `/home/axis/openclaw/trello-config.json`
**Основной скрипт:** `/home/axis/openclaw/trello.py`

**Переменные окружения (установлены глобально):**
```
TRELLO_API_KEY=99928ded9d9a190f208869202e4e5688
TRELLO_TOKEN=ATTA5e81a47...
```

---

## 📋 ДОСКИ И КОЛОНКИ

| Доска | ID | Ключ |
|-------|----|------|
| **Производство** | `697ea1c3b95f7266bd54f96b` | `production` |
| **Стратегия** | `6981a0e378e59c2466b8ab87` | `strategy` |

### Колонки Производство:
- `backlog` — Очередь
- `inProgress` — В работе
- `today` — Сегодня
- `done` — Готово

### Колонки Стратегия:
- `идеи`, `цели_квартала`, `этот_месяц`, `внедряю`, `внедрено`, `метрики`

---

## ⚡ КОМАНДЫ (используй через exec tool)

### Создать карточку
```bash
python3 /home/axis/openclaw/trello.py create production 'Название задачи' backlog 'Описание'
```

### Прочитать карточку
```bash
python3 /home/axis/openclaw/trello.py read <card_id>
```

### Переместить карточку (изменить статус)
```bash
python3 /home/axis/openclaw/trello.py move <card_id> production inProgress
```

### Посмотреть список задач
```bash
python3 /home/axis/openclaw/trello.py list production backlog
```

### Получить статус (всех досок)
```bash
python3 /home/axis/openclaw/trello-report.py status
```

### Утренний отчет
```bash
python3 /home/axis/openclaw/trello-report.py morning
```

---

## 🤖 КОГДА АГЕНТ ДОЛЖЕН СОЗДАВАТЬ КАРТОЧКИ

| Ситуация | Действие |
|----------|----------|
| Поставлена задача по формуле делегирования | `create` в `backlog` |
| Задача взята в работу | `move` → `inProgress` |
| Задача выполнена | `move` → `done` |
| Задача потеряла смысл | `move` → `notRelevant` |

---

## 📝 ПРИМЕР ПОЛНОГО ЦИКЛА ЗАДАЧИ (Ops агент)

```bash
# 1. Создать задачу на планерке
python3 /home/axis/openclaw/trello.py create production \
  'Подготовить 3 концепции фасада для проекта C3' \
  backlog \
  'Ответственный: Мирас. Срок: 20.02.2026. ЦКП: 3 файла с концепциями.'

# 2. Взять в работу
python3 /home/axis/openclaw/trello.py move <card_id> production inProgress

# 3. Закрыть задачу
python3 /home/axis/openclaw/trello.py move <card_id> production done
```

---

## ✅ ТЕСТ ПРОЙДЕН

**Дата:** 2026-02-17
**Исполнитель:** DevOps агент
**Результат:** Карточка создана автономно → https://trello.com/c/13smwtdN
**Вывод:** Агенты могут работать с Trello без участия Руслана.

---
## 📝 Аттестация
Прочитал регламент? Пройди короткую проверку:
🔗 [Пройти аттестацию](https://docs.google.com/forms/d/e/1FAIpQLSePKxyLDt8to-cvcUY29xbrFvilE-eKJAFz8-XCZtBGrTJP5A/viewform)
