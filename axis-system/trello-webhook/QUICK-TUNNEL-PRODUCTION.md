# Quick Tunnel Production Solution
## Автоматическая переустановка webhooks при изменении URL

### Проблема
Quick Tunnel (Cloudflare) генерирует новый URL при каждом перезапуске:
- Перезагрузка WSL/сервера → новый URL
- Webhooks на Trello остаются со старым URL → события не приходят
- Ручная переустановка webhooks = downtime 

### Решение
**Автоматическая детекция и переустановка webhooks** при изменении URL.

### Компоненты

1. **`auto-update-webhooks.sh`** — основной скрипт
   - Извлекает текущий URL из логов туннеля
   - Сравнивает с сохранённым в `.tunnel_url`
   - При изменении: удаляет старые → устанавливает новые webhooks
   - Время работы: ~10-15 секунд

2. **`restart-tunnel.sh`** — wrapper для рестарта
   - Останавливает старый туннель
   - Запускает новый
   - Автоматически вызывает `auto-update-webhooks.sh`

### Использование

#### Обычная работа (автоматически)
После рестарта WSL/сервера:
```bash
cd /home/axis/openclaw/axis-system/trello-webhook
./start.sh  # запустит и webhook-сервер, и туннель с auto-update
```

#### Ручной рестарт туннеля
```bash
./restart-tunnel.sh
```

#### Проверка статуса
```bash
# Текущий URL туннеля
cat .tunnel_url

# Логи автоматического обновления
tail -f logs/webhook-auto-update.log

# Логи туннеля
tail -f logs/tunnel.log

# Список активных webhooks
python3 setup-trello-webhooks.py --list
```

### Тестирование
Протестировано **2 марта 2026, 05:34 GMT+5**:

**Сценарий:** Принудительный рестарт туннеля (симуляция рестарта WSL)

**Результат:**
```
Старый URL: https://resistant-publication-snowboard-bargains.trycloudflare.com
Новый URL:  https://respected-republic-alternative-hay.trycloudflare.com

Время автоматического обновления: 12 секунд
Webhooks переустановлены: 5/5 (C1, C2, C3, C5, Стратегия)
Статус: ✅ Все webhooks работают
```

### Архитектура

```
Рестарт WSL/сервера
       ↓
start.sh запускается
       ↓
Туннель стартует с новым URL
       ↓
(через 10 сек)
       ↓
auto-update-webhooks.sh
       ↓
Сравнение URL (текущий vs сохранённый)
       ↓
Если изменился:
  1. Удалить старые webhooks
  2. Установить новые с новым URL
  3. Сохранить новый URL в .tunnel_url
       ↓
✅ Система работает с новым URL
```

### Преимущества vs Named Tunnel

| Критерий | Quick Tunnel + Auto-update | Named Tunnel |
|----------|---------------------------|--------------|
| **Настройка** | 2 минуты | 20+ минут (требует Cloudflare auth) |
| **Стабильность URL** | Меняется, но автофикс за 10-15 сек | Постоянный |
| **Downtime при рестарте** | 10-15 секунд | 0 секунд |
| **Зависимости** | Только cloudflared | Cloudflared + Cloudflare аккаунт + DNS |
| **WSL совместимость** | ✅ Отлично | ⚠️ Требует браузерную авторизацию |

### Когда нужен Named Tunnel?
- Production-сервер с частыми рестартами (> 10 раз в день)
- SLA требует zero-downtime
- Готов потратить 30+ минут на настройку Cloudflare

### Fallback
Если webhook-система упала, **cron job `1e5ea293`** продолжает обновлять `axis-state.json` раз в час.

### Логи

- **`logs/webhook-auto-update.log`** — история автоматических обновлений
- **`logs/tunnel.log`** — логи Cloudflare туннеля
- **`logs/webhook.log`** — входящие события от Trello
- **`logs/events.log`** — детали событий

### Мониторинг

Проверка здоровья системы:
```bash
# Webhook-сервер работает?
curl http://localhost:18790/health

# Туннель работает?
curl $(cat .tunnel_url)/health

# Последнее обновление webhooks
tail -1 logs/webhook-auto-update.log
```

---

**Статус:** ✅ Production-ready  
**Тестирование:** Пройдено 2 марта 2026  
**Рекомендация:** Использовать для WSL и быстрого деплоя
