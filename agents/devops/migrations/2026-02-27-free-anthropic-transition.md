# MIGRATION: Переход на Free Anthropic & Multi-Level Fallbacks
**Дата:** 2026-02-27
**Автор:** DevOps Agent
**Статус:** ✅ УСПЕХ

---

## 🎯 Цель
Полностью уйти от платного использования Anthropic API Key в повседневных задачах, сохранив доступ к Claude Sonnet/Opus через бесплатные методы (Setup Tokens + Google Antigravity), и настроить "бессмертную" систему фоллбэков.

## 🛠 Проблема
1. Система упорно использовала платный `ANTHROPIC_API_KEY`, игнорируя настройки конфига.
2. Переменная окружения "залипла" в `systemd` unit файле и не удалялась через `unset`.
3. Лимиты на одном setup-token быстро заканчивались.

## ✅ Решение (Ход работ)

### 1. Зачистка "Бессмертной" переменной
- **Диагностика:** Opus (Subagent) обнаружил, что переменная `ANTHROPIC_API_KEY` была жестко прописана в `openclaw-gateway.service`.
- **Действие:** Полная переустановка сервиса (`service uninstall` -> `install`), удаление ключа из всех конфигов.
- **Результат:** Gateway чист, конфликтов нет.

### 2. Внедрение Setup-Tokens (Double Power)
Настроено **ДВА** независимых аккаунта для обхода Rate Limits:
1. `anthropic:ruzike-ant-setup-token` (Основной)
2. `anthropic:toolruzik-eant-setup-token` (Резервный)

### 3. Google Antigravity (x5)
Подключено 5 OAuth-аккаунтов для доступа к Claude через Google:
- `archvizbusiness@gmail.com`
- `design3d.kz@gmail.com`
- `ruslanshakirzhanovich@gmail.com`
- `axis.intelekt@gmail.com`
- `ruzike@gmail.com`

### 4. Gemini Rotation (x4)
Настроена ротация 4-х API ключей Google для модели Gemini 3.1 Pro.

---

## 🛡 "ЯДЕРНЫЙ ЩИТ" (Fallback Chain)

Настроена **строгая иерархия** использования моделей. Система переходит на следующий уровень ТОЛЬКО если предыдущий отказал.

| Уровень | Провайдер | Метод | Стоимость |
|:---:|---|---|---|
| **1 (Primary)** | **Anthropic** | Setup-Tokens (x2) | 🟢 **БЕСПЛАТНО** |
| **2 (Fallback)** | **Google Antigravity** | OAuth (x5 Accounts) | 🟢 **БЕСПЛАТНО** |
| **3 (Fallback)** | **Google Gemini** | API Keys (x4 Rotation) | 🟢 **БЕСПЛАТНО** |
| **4 (Last Resort)**| **Anthropic API** | Backup Key | 🔴 **ПЛАТНО** |

**Логика конфига (`openclaw.json`):**
```json
"defaults": {
  "model": {
    "primary": "anthropic/claude-sonnet-4-6",
    "fallbacks": [
      "google-antigravity/claude-sonnet-4-5", // Сначала бесплатный Claude от Google
      "google/gemini-3.1-pro-preview",        // Потом бесплатный Gemini
      "anthropic/claude-sonnet-4-5"           // В самом конце платный Claude (резерв)
    ]
  }
}
```

## 📂 Файлы конфигурации
- **Auth:** `~/.openclaw/agents/main/agent/auth-profiles.json` (содержит токены)
- **Config:** `~/.openclaw/openclaw.json` (содержит логику fallbacks)

---
**Итог:** Система защищена от блокировок в 11 слоёв (2 setup + 5 antigravity + 4 gemini) перед тем, как потратить хоть цент.
