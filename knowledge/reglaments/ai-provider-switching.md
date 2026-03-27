# Регламент: Переключение моделей AI

**Версия:** 3.0  
**Дата:** 2026-02-18  
**Автор:** Ops агент  
**Статус:** ✅ Действующий  

---

## 1. Провайдеры и модели

| Провайдер | Описание | Стоимость |
|-----------|----------|-----------|
| **claude-max** | Claude Max/Pro подписка (через локальный прокси) | $0 (входит в подписку) |
| **anthropic** | Официальный Anthropic API | Платно (per token) |
| **zai** | GLM-5, GLM-4.7-Flash | $0 (бесплатно) |

---

## 2. Команды переключения

### 🟢 Основной режим — Max/Pro подписка (бесплатно):
```
/model pi-sonnet   ← Claude Sonnet 4 (Max) — повседневная работа
/model pi-opus     ← Claude Opus 4 (Max) — сложные задачи
/model pi-haiku    ← Claude Haiku 4 (Max) — быстро/дёшево
```

### 🔄 Когда исчерпаны лимиты Max — переключиться на API:
```
/model sonnet      ← Claude Sonnet 4.5 (API)
/model opus        ← Claude Opus 4.6 (API)
/model haiku       ← Claude Haiku 4.5 (API)
```

### 🆓 Резервный вариант — без лимитов и без затрат:
```
/model glm5        ← GLM-5 (бесплатно, z.ai)
```

### 📋 Навигация:
```
/model list        ← полный список доступных моделей
/model status      ← статус текущей модели
/status            ← полный статус сессии
```

---

## 3. Шпаргалка — что делать когда

| Ситуация | Команда |
|----------|---------|
| Обычная работа | `/model pi-sonnet` |
| Сложный анализ / стратегия | `/model pi-opus` |
| Max лимит исчерпан | `/model sonnet` |
| Нужна мощь, Max лимит исчерпан | `/model opus` |
| API тоже исчерпан | `/model glm5` |
| Лимиты Max восстановились | `/model pi-sonnet` |

---

## 4. SLA — что делать при сбоях

### При сообщении "лимит исчерпан" (Max/Pro):
1. Переключить: `/model sonnet`
2. Лимит сбрасывается через 5 часов (session) или в понедельник (weekly)
3. Уведомить Руслана если критично

### При ошибке Anthropic API:
1. Переключить на Max: `/model pi-sonnet`
2. Или на GLM-5: `/model glm5`
3. Проверить статус: https://status.anthropic.com

### При недоступности прокси (claude-max не отвечает):
1. Перезапустить прокси: `bash /home/axis/openclaw/scripts/start-claude-max-proxy.sh`
2. Переключить на API: `/model sonnet`
3. Написать Руслану если прокси не поднимается

---

## 5. Техническая справка

- **claude-max-api-proxy** запущен на `http://localhost:3456`
- Использует **OAuth аккаунт** `toolruzike@gmail.com` (Max/Pro подписка)
- Автозапуск: `@reboot` в crontab
- Логи: `/tmp/claude-max-api.log`
- Перезапуск: `/home/axis/openclaw/scripts/start-claude-max-proxy.sh`

---

*Регламент обновляется при изменении инфраструктуры.*  
*Следующий плановый пересмотр: 2026-03-18*
