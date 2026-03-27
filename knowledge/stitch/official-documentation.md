# Google Stitch — Полная документация для агента

> **Версия:** март 2026 | **Источник:** stitch.withgoogle.com/docs + официальные репозитории Google Labs

---

## 1. Что такое Google Stitch

Google Stitch — это AI-инструмент от Google Labs для генерации пользовательских интерфейсов (UI) из текстовых запросов, изображений, скетчей и голосовых команд. Результат — высококачественные макеты с готовым frontend-кодом (HTML/CSS/React).

**Ключевые факты:**
- Запущен на Google I/O, май 2025
- Основан на моделях Gemini (Gemini 3 Flash / Gemini 3.1 Pro)
- Полностью бесплатен (с месячными квотами)
- Работает в браузере: [stitch.withgoogle.com](https://stitch.withgoogle.com)
- Экспериментальный проект Google Labs

---

## 2. Архитектура и технологии

| Компонент | Описание |
|---|---|
| **AI-движок** | Google Gemini 3 Flash (быстрый) / Gemini 3.1 Pro (точный) |
| **Canvas** | AI-native бесконечный холст (Infinite Canvas) |
| **Design Agent** | Агент, отслеживающий весь контекст проекта |
| **Voice Engine** | Голосовой ввод с real-time обновлениями |
| **Prototyping** | Связывание экранов в интерактивные прототипы |
| **Code Export** | HTML + CSS + React (семантический, production-ready) |
| **MCP Server** | `stitch.googleapis.com/mcp` — API-доступ для агентов |
| **SDK** | `@google/stitch-sdk` — официальный Node.js SDK |

---

## 3. Доступ и аутентификация

### 3.1 Веб-интерфейс
1. Перейти на [stitch.withgoogle.com](https://stitch.withgoogle.com)
2. Войти через Google-аккаунт
3. Выбрать тип проекта: Mobile или Web

### 3.2 API-ключ (для агентов)
```
Stitch → иконка профиля (правый верхний угол) 
→ Stitch Settings → API Keys → Create Key
```
Скопировать ключ. Использовать в переменной окружения:
```bash
export STITCH_API_KEY="ваш-api-ключ"
```

### 3.3 Application Default Credentials (ADC)
Для использования с собственным Google Cloud проектом:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
gcloud beta services mcp enable stitch.googleapis.com
```

---

## 4. Режимы генерации

| Режим | Модель | Скорость | Качество | Когда использовать |
|---|---|---|---|---|
| **Standard** | Gemini 3 Flash | 2–5 сек | Хорошее | Быстрое прототипирование, итерации |
| **Experimental** | Gemini 3.1 Pro | ~90 сек | Высокое | Финальный дизайн, сложные интерфейсы |

---

## 5. Основные возможности

### 5.1 Генерация UI из текста (Vibe Design)
Описываете бизнес-цель или «ощущение» интерфейса — Stitch генерирует несколько вариантов дизайна.

**Пример эффективного промпта:**
```
Мобильный дашборд для трекинга финансов.
Тема: тёмная, минималистичная, как Stripe.
Компоненты: хедер с балансом, карточки категорий (Еда, Транспорт),
список последних транзакций.
Требования: одноручное использование, WCAG 2.1, скруглённые углы.
```

**Структура хорошего промпта:**
1. `Контекст` — тип приложения и платформа
2. `Компоненты` — навбар, карточки, графики
3. `Визуальный стиль` — цвета, темы, ощущение
4. `Ограничения` — доступность, размеры, правила

### 5.2 Генерация из изображения / скетча
- Загрузить скриншот, wireframe или нарисованный от руки скетч
- Stitch преобразует в high-fidelity макет
- Поддерживаются форматы: PNG, JPG, PDF

### 5.3 Голосовой режим (Voice Canvas)
- Говорить напрямую с холстом
- Агент даёт real-time критику дизайна
- Примеры команд:
  - *"Покажи мне три варианта меню"*
  - *"Измени цветовую палитру на синюю"*
  - *"Создай landing page — задай мне вопросы"*

### 5.4 Интерактивные прототипы
- Выбрать 2+ экрана → определить переходы → нажать **Play**
- Кнопка **Generate Next Screen** — Stitch автоматически создаёт логичный следующий экран
- Поддерживаются горячие точки (clickable hotspots)

### 5.5 Ручное редактирование (с марта 2026)
- Кликнуть на любой текстовый элемент → изменить напрямую
- Замена изображений
- Настройка отступов и spacing

### 5.6 DESIGN.md — Дизайн-система для агентов
Stitch создаёт файл `DESIGN.md` — markdown-документацию с правилами дизайн-системы проекта:
- Цветовые токены
- Типография
- Правила компонентов
- Совместим с AI-агентами (Antigravity, Gemini CLI, Claude Code, Cursor)

---

## 6. Экспорт дизайна

| Метод | Что получаете | Как |
|---|---|---|
| **HTML/CSS** | Семантический код | Вкладка «Code» на экране |
| **React** | Компоненты | Вкладка «Code» → React |
| **Figma** | Редактируемые слои + Auto Layout | Кнопка «Copy to Figma» |
| **Google AI Studio** | Прямая интеграция | Кнопка «Open in AI Studio» |
| **Google Jules** | AI-ассистент разработки | Кнопка «Export to Jules» |
| **ZIP-архив** | Все ассеты и код | Кнопка «Download ZIP» |
| **MCP** | Для coding-агентов | Через Stitch MCP server |

**Ограничения экспорта кода:**
- По умолчанию: HTML + TailwindCSS
- React: поддерживается
- Vue / Angular: НЕ поддерживается (нужна ручная конвертация)
- Backend-логика: НЕ включена
- Адаптивность: требует доработки под продакшн

---

## 7. MCP Server (для агентов)

### 7.1 Официальный MCP endpoint
```
https://stitch.googleapis.com/mcp
```

### 7.2 Быстрая настройка через npx
```bash
npx @_davideast/stitch-mcp init
```
Мастер установки автоматически настроит gcloud, аутентификацию и конфиг MCP-клиента.

### 7.3 Конфигурация MCP-клиента

**С API-ключом:**
```json
{
  "mcpServers": {
    "stitch": {
      "command": "npx",
      "args": ["-y", "stitch-mcp"],
      "env": {
        "STITCH_API_KEY": "ваш-api-ключ"
      }
    }
  }
}
```

**С gcloud ADC:**
```json
{
  "mcpServers": {
    "stitch": {
      "command": "npx",
      "args": ["@_davideast/stitch-mcp", "proxy"],
      "env": {
        "STITCH_USE_SYSTEM_GCLOUD": "1"
      }
    }
  }
}
```

**С Google Cloud Project:**
```json
{
  "mcpServers": {
    "stitch": {
      "command": "npx",
      "args": ["-y", "stitch-mcp"],
      "env": {
        "GOOGLE_CLOUD_PROJECT": "ваш-project-id"
      }
    }
  }
}
```

### 7.4 Поддерживаемые клиенты
- VS Code
- Cursor
- Claude Code
- Gemini CLI
- Codex
- OpenCode
- Antigravity

### 7.5 Доступные MCP-инструменты

| Инструмент | Описание |
|---|---|
| `generate_screen_from_text` | Генерация экрана по текстовому промпту |
| `get_screen_code` | Получение HTML-кода конкретного экрана |
| `get_screen_image` | Скриншот экрана (base64) |
| `build_site` | Сборка сайта из проекта (экраны → роуты) |
| `list_projects` | Список всех проектов |
| `list_screens` | Все экраны в проекте |

### 7.6 CLI-команды (stitch-mcp)

```bash
# Просмотр всех проектов
npx @_davideast/stitch-mcp view --projects

# Просмотр конкретного экрана
npx @_davideast/stitch-mcp view --project <project-id> --screen <screen-id>

# Запуск локального dev-сервера со всеми экранами
npx @_davideast/stitch-mcp serve -p <project-id>

# Сборка Astro-сайта из проекта
npx @_davideast/stitch-mcp site -p <project-id>

# Вызов любого MCP-инструмента напрямую
npx @_davideast/stitch-mcp tool [toolName]

# Список всех инструментов
npx @_davideast/stitch-mcp tool

# Просмотр схемы инструмента
npx @_davideast/stitch-mcp tool [toolName] -s

# Диагностика
npx @_davideast/stitch-mcp doctor --verbose

# Выход / сброс аутентификации
npx @_davideast/stitch-mcp logout --force --clear-config
```

**Навигация в браузере view:**
- `↑ ↓` — навигация
- `Enter` — углубиться в структуру
- `c` — скопировать значение
- `s` — превью HTML в браузере
- `o` — открыть проект в Stitch
- `q` — выход

---

## 8. Официальный SDK (@google/stitch-sdk)

### 8.1 Установка
```bash
npm install @google/stitch-sdk
```

### 8.2 Базовое использование (singleton)
```javascript
import { stitch } from "@google/stitch-sdk";
// STITCH_API_KEY читается из переменной окружения автоматически

const projects = await stitch.projects();
```

### 8.3 Инициализация с параметрами
```javascript
import { Stitch, StitchToolClient } from "@google/stitch-sdk";

const client = new StitchToolClient({
  apiKey: "ваш-api-ключ",
  baseUrl: "https://stitch.googleapis.com/mcp",
  timeout: 300_000, // 5 минут (генерация может занимать долго)
});

const sdk = new Stitch(client);
const projects = await sdk.projects();
```

**Аутентификация:** требует либо `apiKey`, либо `accessToken` + `projectId`.

### 8.4 Низкоуровневый доступ к инструментам
```javascript
import { StitchToolClient } from "@google/stitch-sdk";

const client = new StitchToolClient({ apiKey: "..." });
const result = await client.callTool("generate_screen_from_text", {
  prompt: "Страница входа в систему, тёмная тема",
  model: "gemini-3-pro"
});
await client.close();
```

### 8.5 Интеграция с Vercel AI SDK
```javascript
import { generateText, stepCountIs } from "ai";
import { stitchTools } from "@google/stitch-sdk/ai";

const { text } = await generateText({
  model: yourModel,
  tools: stitchTools(), // Все Stitch MCP инструменты как Vercel AI Tools
  prompt: "Создай страницу входа",
  stopWhen: stepCountIs(5),
});
```

### 8.6 Создание собственного MCP-прокси
```javascript
import { StitchProxy } from "@google/stitch-sdk";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const proxy = new StitchProxy({ apiKey: "..." });
const transport = new StdioServerTransport();
await proxy.start(transport);
```

---

## 9. Agent Skills (Stitch Skills)

Репозиторий: `github.com/google-labs-code/stitch-skills`

### 9.1 Установка скилла
```bash
# Список доступных скиллов
npx skills add google-labs-code/stitch-skills --list

# Установка конкретного скилла глобально
npx skills add google-labs-code/stitch-skills --skill stitch-design --global

# Установка React-компонентов скилла
npx skills add google-labs-code/stitch-skills --skill react:components --global
```

### 9.2 Основные скиллы

| Скилл | Описание |
|---|---|
| `stitch-design` | Главный скилл. Улучшение промптов, синтез дизайн-системы (.stitch/DESIGN.md), генерация/редактирование экранов |
| `react:components` | Конвертация Stitch-экранов в React-компоненты |

### 9.3 Совместимость
- Antigravity
- Gemini CLI
- Claude Code
- Cursor

---

## 10. Квоты и тарифы

| Параметр | Бесплатный план | Pro ($20/месяц) |
|---|---|---|
| Стандартные генерации | ~350/месяц | Безлимит |
| Экспериментальные генерации | ~50/месяц | Безлимит |
| Сброс квоты | 1-е число месяца (UTC) | — |
| Приоритет очереди | Нет | Есть |
| Офлайн PWA | Нет | В роадмапе 2026 |
| MCP API | Бесплатно | Бесплатно |

---

## 11. Интеграционный пайплайн (рекомендуемый workflow)

```
Идея
  │
  ▼
[Stitch] — Text/Image/Voice Input
  │  Генерация за 2-90 сек
  ▼
[Stitch Canvas] — Итерации, прототипы, DESIGN.md
  │
  ├──── Figma (финальный дизайн, дизайн-система)
  │
  ├──── AI Studio / Jules (разработка приложения)
  │
  ├──── MCP → Claude Code / Cursor / Antigravity
  │         (агентная разработка фронтенда)
  │
  └──── ZIP / HTML+CSS (прямое использование в коде)
```

**Этапы:**
1. **Ideation (Stitch):** Быстрая валидация направлений дизайна (2–5 сек/вариант)
2. **Design (Figma):** Дизайн-система, pixel-perfect доработка, командное ревью
3. **Development:** Используйте экспортированный код как основу
4. **AI Integration:** Подключение backend через API (Gemini, Claude и др.)

---

## 12. Расширенные инструменты (stitch-mcp-auto)

Расширенный MCP-сервер с 19 дополнительными инструментами:

### 12.1 Установка
```bash
npx -p stitch-mcp-auto stitch-mcp-auto-setup
```

### 12.2 Дополнительные инструменты

| Инструмент | Описание |
|---|---|
| Тренды 2025-2026 | Glassmorphism, bento-grid, gradient-mesh в генерации |
| Style Guide Generator | Генерация документации из существующего дизайна |
| Design System Export | Экспорт токенов, компонентов, документации для разработчиков |
| Asset Generator | Логотипы, иконки, иллюстрации через Gemini 3 Pro |
| Accessibility Check | Проверка на WCAG-соответствие |
| Responsive Variants | Генерация мобильной/десктопной версии |

### 12.3 Workflow-команды

| Claude Code | Gemini CLI | Codex CLI |
|---|---|---|
| `/design login page` | `/stitch:design login page` | `$stitch-design login page` |
| `/design-system settings` | `/stitch:design-system settings` | `$stitch-design-system settings` |
| `/design-flow onboarding` | `/stitch:design-flow onboarding` | `$stitch-design-flow onboarding` |
| `/design-qa` | `/stitch:design-qa` | `$stitch-design-qa` |
| `/generate-asset logo` | `/stitch:generate-asset logo` | `$stitch-generate-asset logo` |

### 12.4 Полный пайплайн (один промпт)
```
/design-full "мобильное приложение для трекинга финансов"
```
→ Автогенерация: логотип + иконки + hero + все экраны UI

---

## 13. Решение проблем

### Аутентификация

| Проблема | Решение |
|---|---|
| Ошибка 401 | `npx @_davideast/stitch-mcp logout --force && npx @_davideast/stitch-mcp init` |
| URL аутентификации не открывается | Искать URL `https://accounts.google.com` в терминале (таймаут 5 сек) |
| Ошибки в WSL | Открыть `http://localhost:8086` в браузере Windows |
| Proxy debug-лог | `/tmp/stitch-proxy-debug.log` |

### Требования для ADC

- Роль: Owner или Editor в Google Cloud проекте
- Billing должен быть включён
- Stitch API должен быть активирован

### Генерация экранов

| Проблема | Решение |
|---|---|
| TCP connection drop (частый при генерации) | Использовать Go MCP server с автовосстановлением |
| Генерация > 10 минут | Нормально для Experimental режима; использовать `generation_status` tool |
| Низкое качество результата | Переключиться на Gemini 3.1 Pro, детализировать промпт |

### Диагностика
```bash
npx @_davideast/stitch-mcp doctor --verbose
```

---

## 14. Ограничения и важные оговорки

- **Только frontend:** Нет backend-логики, API-подключений, state management
- **Нет мультиюзерного режима:** Только одиночные сессии (на март 2026)
- **Не замена Figma:** Инструмент для rapid prototyping, не для дизайн-систем
- **Экспериментальный статус:** Функции могут меняться без предупреждения
- **Точность генерации:** 80–90%; финальная полировка требуется
- **Код под продакшн:** Нужна адаптивность, интерактивность, state management
- **Конфиденциальность:** Не загружать конфиденциальные макеты; маскировать данные клиентов

---

## 15. Полезные ссылки

| Ресурс | URL |
|---|---|
| Stitch App | [stitch.withgoogle.com](https://stitch.withgoogle.com) |
| Документация | [stitch.withgoogle.com/docs](https://stitch.withgoogle.com/docs) |
| Official SDK (GitHub) | github.com/google-labs-code/stitch-sdk |
| Stitch Skills (GitHub) | github.com/google-labs-code/stitch-skills |
| MCP CLI (davideast) | github.com/davideast/stitch-mcp |
| MCP auto-setup | github.com/GreenSheep01201/stitch-mcp-auto |
| Gemini CLI Extension | github.com/gemini-cli-extensions/stitch |
| MCP Endpoint | https://stitch.googleapis.com/mcp |

---

*Документ актуален на март 2026. Google Stitch — активно развивающийся инструмент. Проверяйте официальную документацию для последних обновлений.*
