# AXIS Mobile App — Техническое Задание
**Версия:** 1.0  
**Дата:** 2026-03-20  
**Платформа:** Flutter 3.x (Android + iOS)  
**Автор:** Mobile Developer Agent

---

## 1. ОБЗОР ПРОДУКТА

AXIS Mobile App — единая точка управления компанией с телефона. Собственник и команда общаются с AI-агентами, следят за KPI, получают алерты и управляют процессами в реальном времени.

**Backend:** OpenClaw Gateway  
- Local: `ws://127.0.0.1:18789`  
- Remote: Cloudflare Tunnel (HTTPS/WSS)  
- Auth Token: `YOUR_GATEWAY_TOKEN`  
- Protocol: WebSocket JSON, Protocol v3

---

## 2. АРХИТЕКТУРА

### 2.1 Общая схема

```
┌─────────────────────────────────────────────┐
│              AXIS Mobile App                │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Flutter │  │ Riverpod │  │  Router  │  │
│  │   UI     │  │  State   │  │  GoRoute │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       └─────────────┴─────────────┘         │
│                      │                      │
│              ┌───────┴───────┐              │
│              │ Gateway Client │              │
│              │  (WebSocket)   │              │
│              └───────┬───────┘              │
│                      │                      │
│  ┌───────────────────┼───────────────────┐  │
│  │ SQLite Cache   SharedPrefs   FCM Push │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                       │
              Cloudflare Tunnel
                       │
         ┌─────────────┴─────────────┐
         │   OpenClaw Gateway        │
         │   ws://127.0.0.1:18789    │
         └───────────────────────────┘
```

### 2.2 State Management

**Riverpod** (flutter_riverpod ^2.x):
- `GatewayProvider` — WebSocket соединение, авторизация
- `SessionsProvider` — список сессий/агентов
- `ChatProvider(sessionKey)` — история чата конкретного агента
- `DashboardProvider` — данные дашбордов (KPI, ритуалы)
- `NotificationsProvider` — очередь push-уведомлений
- `AuthProvider` — токен, device identity, pairing status

### 2.3 Навигация

**GoRouter** — декларативный routing:

```
/                     → SplashScreen (check auth)
/login                → LoginScreen
/home                 → HomeScreen (shell route)
  /chat               → AgentListScreen
  /chat/:agentId      → ChatScreen
  /groups             → GroupChatListScreen
  /groups/:groupId    → GroupChatScreen
  /dashboards         → DashboardsScreen
  /dashboards/kpi     → KPIDashboardScreen
  /dashboards/rituals → RitualsDashboardScreen
  /dashboards/office  → OfficeDashboardScreen
  /dashboards/auto    → AutomationDashboardScreen
  /notifications      → NotificationsScreen
  /settings           → SettingsScreen
  /settings/agents    → AgentsSettingsScreen
```

### 2.4 Роль приложения в Gateway

Приложение подключается как **operator** (для чата) и опционально как **node** (для камеры, геолокации, голоса):

```dart
// Operator connect params
{
  "role": "operator",
  "scopes": ["operator.read", "operator.write"],
  "client": {
    "id": "axis-mobile",
    "version": "1.0.0",
    "platform": "android" | "ios",
    "mode": "operator"
  },
  "caps": ["camera", "location", "voice"],
  "commands": ["camera.snap", "location.get"],
  "auth": { "token": "YOUR_GATEWAY_TOKEN" }
}
```

---

## 3. ЭКРАНЫ (WIREFRAMES)

### 3.1 SplashScreen
```
┌─────────────────────┐
│                     │
│      [AXIS Logo]    │
│                     │
│   Connecting...     │
│   ████████░░░░      │
│                     │
└─────────────────────┘
```
- Проверяет сохранённый device token
- При наличии → авто-коннект к Gateway
- При отсутствии → /login

### 3.2 LoginScreen
```
┌─────────────────────┐
│     AXIS            │
│                     │
│ Gateway URL:        │
│ [________________]  │
│                     │
│ Token:              │
│ [________________]  │
│                     │
│   [Подключиться]    │
│                     │
│ или [QR Scan] 📷    │
└─────────────────────┘
```
- Ввод Gateway URL + Token
- QR-сканирование (формат: `openclaw://gateway?url=...&token=...`)
- Сохранение в SharedPreferences
- Handshake → device token → /home

### 3.3 HomeScreen (Bottom Nav Shell)
```
┌─────────────────────┐
│ AXIS          🔔 ⚙️ │
├─────────────────────┤
│                     │
│   [Content Area]    │
│                     │
├─────────────────────┤
│ 💬 Chat  📊 Dash  🔔│
└─────────────────────┘
```
- 3 вкладки: Chat, Dashboards, Notifications
- Badge на иконке при новых сообщениях
- Header с именем текущего экрана

### 3.4 AgentListScreen
```
┌─────────────────────┐
│ 💬 Агенты      🔍   │
├─────────────────────┤
│ 👤 main         ●  │
│    Руслан, привет..  │
│    14:32    [2]     │
├─────────────────────┤
│ 🤖 devops           │
│    Gateway OK       │
│    13:15            │
├─────────────────────┤
│ 📊 ops              │
│    KPI обновлён     │
│    12:00            │
├─────────────────────┤
│ [+ Групповые чаты]  │
└─────────────────────┘
```
Агенты (11 штук):
`main, devops, ops, qc, tech, hr, finance, shket, draftsman, strategy, coach`

Группы:
- Аэропорт (-1003662320078)
- AXIS Staff (-1003887996783)

### 3.5 ChatScreen
```
┌─────────────────────┐
│ ← 🤖 main      ···  │
│    Online           │
├─────────────────────┤
│                     │
│ [Агент: Готов!   ] │
│ 14:30               │
│                     │
│       [Ты: Привет] │
│             14:31   │
│                     │
│ [Агент: Привет!  ] │
│ 14:31               │
│                     │
├─────────────────────┤
│ 📎 🎤 [Сообщение] ➤│
└─────────────────────┘
```
- Markdown рендеринг ответов агента
- Typing indicator при стриминге
- Attach: фото 📷, файл 📎
- Голосовое сообщение 🎤 (hold to record)
- TTS воспроизведение ответа агента (кнопка 🔊)
- Стриминг токенов в реальном времени (WebSocket)

### 3.6 DashboardsScreen
```
┌─────────────────────┐
│ 📊 Дашборды         │
├─────────────────────┤
│ ┌────────┐ ┌──────┐ │
│ │  KPI   │ │Ритуа-│ │
│ │ 📈     │ │лы 📋 │ │
│ └────────┘ └──────┘ │
│ ┌────────┐ ┌──────┐ │
│ │ Офис   │ │Авто- │ │
│ │ 🏢     │ │мат.⚙️│ │
│ └────────┘ └──────┘ │
└─────────────────────┘
```

### 3.7 KPIDashboardScreen
```
┌─────────────────────┐
│ ← KPI    Сегодня ▼  │
├─────────────────────┤
│ Выручка             │
│ ████████░░  82%     │
│ 410K / 500K ₸       │
├─────────────────────┤
│ Лиды сегодня        │
│ ●●●●●●●●●○○  8/11  │
├─────────────────────┤
│ Конверсия           │
│      73% ↑          │
├─────────────────────┤
│ [Агенты] [Кроны]    │
│  ✅ 11    ✅ 29     │
└─────────────────────┘
```

### 3.8 RitualsDashboardScreen
```
┌─────────────────────┐
│ ← Ритуалы  Пн 20/3 │
├─────────────────────┤
│ Утро                │
│ ✅ Стендап 09:00    │
│ ✅ KPI-брифинг      │
│ ⬜ Фокус-блок       │
├─────────────────────┤
│ День                │
│ ⬜ Обед-анализ      │
│ ⬜ Командный созвон │
├─────────────────────┤
│ Вечер               │
│ ⬜ Итоги дня        │
│ ⬜ План на завтра   │
└─────────────────────┘
```

### 3.9 NotificationsScreen
```
┌─────────────────────┐
│ 🔔 Уведомления      │
├─────────────────────┤
│ 🚨 СРОЧНО  14:35    │
│ devops: Gateway     │
│ перезапущен         │
├─────────────────────┤
│ ℹ️ ops  14:00       │
│ KPI дашборд обновлён│
├─────────────────────┤
│ ✅ qc  13:45        │
│ Отчёт проверен      │
└─────────────────────┘
```
- Фильтр по агенту / типу (срочные, инфо, задачи)
- Тап → открывает чат с агентом

### 3.10 SettingsScreen
```
┌─────────────────────┐
│ ⚙️ Настройки        │
├─────────────────────┤
│ Gateway URL         │
│ wss://axis.example  │
│                     │
│ Уведомления    🔔 ✓ │
│ TTS голос      🔊 ✓ │
│ Офлайн кэш     💾 ✓ │
│                     │
│ Агенты              │
│ Управление [→]      │
│                     │
│ [Отключиться]       │
└─────────────────────┘
```

---

## 4. API ENDPOINTS

### 4.1 WebSocket Gateway Protocol

**Подключение:**
```
WSS: wss://<cloudflare-tunnel>/ws
или
WS:  ws://127.0.0.1:18789/ws
```

**Handshake Flow:**

```
1. Server → Client: connect.challenge
   { "type": "event", "event": "connect.challenge", 
     "payload": { "nonce": "abc123", "ts": 1737264000000 } }

2. Client → Server: connect (req)
   {
     "type": "req",
     "id": "req_1",
     "method": "connect",
     "params": {
       "minProtocol": 3,
       "maxProtocol": 3,
       "client": { "id": "axis-mobile", "version": "1.0.0", 
                   "platform": "android", "mode": "operator" },
       "role": "operator",
       "scopes": ["operator.read", "operator.write"],
       "caps": ["camera", "location", "voice"],
       "commands": ["camera.snap", "location.get"],
       "permissions": {},
       "auth": { "token": "YOUR_GATEWAY_TOKEN" },
       "locale": "ru-KZ",
       "userAgent": "axis-mobile/1.0.0",
       "device": {
         "id": "<stable-device-fingerprint>",
         "publicKey": "<ed25519-public-key>",
         "signature": "<signed-nonce-payload>",
         "signedAt": 1737264000000,
         "nonce": "abc123"
       }
     }
   }

3. Server → Client: hello-ok (res)
   {
     "type": "res", "id": "req_1", "ok": true,
     "payload": {
       "type": "hello-ok",
       "protocol": 3,
       "policy": { "tickIntervalMs": 15000 },
       "auth": { "deviceToken": "<token>", "role": "operator",
                 "scopes": ["operator.read", "operator.write"] }
     }
   }
```

**Сохранить deviceToken** → использовать для следующих сессий.

### 4.2 Ключевые WS методы

```dart
// Получить список сессий агентов
{
  "type": "req", "id": "req_2",
  "method": "sessions.list",
  "params": {}
}

// Получить историю чата
{
  "type": "req", "id": "req_3",
  "method": "sessions.history",
  "params": {
    "sessionKey": "agent:main:telegram:direct:YOUR_TELEGRAM_ID",
    "limit": 50
  }
}

// Отправить сообщение агенту
{
  "type": "req", "id": "req_4",
  "method": "sessions.send",
  "params": {
    "sessionKey": "agent:main:telegram:direct:YOUR_TELEGRAM_ID",
    "message": "Привет!"
  }
}

// Стримить ответ агента (события)
// Server → Client event:
{
  "type": "event",
  "event": "session.message",
  "payload": {
    "sessionKey": "agent:main:...",
    "message": { "role": "assistant", "content": "Привет!..." },
    "streaming": true
  }
}
```

### 4.3 REST API (дополнительно к WS)

```
GET  /api/status          → статус Gateway
GET  /api/sessions        → список сессий
POST /api/sessions/send   → отправка сообщения
GET  /api/sessions/:key/history  → история

Headers:
  Authorization: Bearer YOUR_GATEWAY_TOKEN
  Content-Type: application/json
```

### 4.4 Push (FCM)

```
Сервер → Firebase FCM → AXIS App

Payload:
{
  "notification": {
    "title": "🚨 devops",
    "body": "Gateway перезапущен"
  },
  "data": {
    "type": "agent_alert",
    "sessionKey": "agent:devops:...",
    "priority": "urgent"
  }
}
```

OpenClaw Gateway отправляет push через FCM при:
- Ответе агента (когда приложение фоновое)
- Срочных эскалациях (крон-алерты)
- Упоминаниях в группах

---

## 5. ТЕХНИЧЕСКИЙ СТЕК

### 5.1 Flutter Packages

```yaml
dependencies:
  flutter:
    sdk: flutter

  # State Management
  flutter_riverpod: ^2.5.1
  riverpod_annotation: ^2.3.5

  # Navigation
  go_router: ^14.0.0

  # WebSocket
  web_socket_channel: ^3.0.0

  # HTTP
  dio: ^5.4.0

  # Local Storage
  shared_preferences: ^2.2.3
  sqflite: ^2.3.3
  path_provider: ^2.1.3

  # Push Notifications
  firebase_core: ^3.0.0
  firebase_messaging: ^15.0.0
  flutter_local_notifications: ^17.0.0

  # Camera & Media
  camera: ^0.11.0
  image_picker: ^1.1.0
  file_picker: ^8.0.0

  # Audio (Voice)
  record: ^5.1.0              # запись голоса
  just_audio: ^0.9.39         # воспроизведение TTS
  flutter_tts: ^4.0.2         # Text-to-Speech

  # UI
  flutter_markdown: ^0.7.3    # рендер markdown
  cached_network_image: ^3.3.1
  shimmer: ^3.0.0             # loading skeleton
  badges: ^3.1.2

  # Geolocation
  geolocator: ^12.0.0
  geocoding: ^3.0.0

  # Crypto (device identity)
  pointycastle: ^3.9.1        # Ed25519 signing
  uuid: ^4.4.0

  # QR Scanner (login)
  mobile_scanner: ^5.0.0

  # Utils
  intl: ^0.19.0
  timeago: ^3.6.1
  connectivity_plus: ^6.0.3

dev_dependencies:
  flutter_test:
    sdk: flutter
  riverpod_generator: ^2.4.3
  build_runner: ^2.4.9
  flutter_launcher_icons: ^0.13.1
  flutter_native_splash: ^2.4.0
```

### 5.2 Структура проекта

```
lib/
├── main.dart
├── app.dart                    # App root, GoRouter setup
├── core/
│   ├── constants.dart          # API URLs, tokens
│   ├── theme.dart              # AXIS brand theme
│   └── router.dart             # GoRouter config
├── gateway/
│   ├── gateway_client.dart     # WebSocket connection
│   ├── gateway_protocol.dart   # JSON models (connect/req/res/event)
│   ├── device_identity.dart    # Ed25519 keypair + signing
│   └── gateway_provider.dart   # Riverpod provider
├── features/
│   ├── auth/
│   │   ├── login_screen.dart
│   │   └── auth_provider.dart
│   ├── chat/
│   │   ├── agent_list_screen.dart
│   │   ├── chat_screen.dart
│   │   ├── chat_provider.dart
│   │   ├── message_bubble.dart
│   │   └── voice_recorder.dart
│   ├── dashboards/
│   │   ├── dashboards_screen.dart
│   │   ├── kpi_dashboard.dart
│   │   ├── rituals_dashboard.dart
│   │   ├── office_dashboard.dart
│   │   ├── automation_dashboard.dart
│   │   └── dashboard_provider.dart
│   ├── notifications/
│   │   ├── notifications_screen.dart
│   │   └── notifications_provider.dart
│   └── settings/
│       └── settings_screen.dart
├── shared/
│   ├── widgets/
│   │   ├── axis_app_bar.dart
│   │   ├── loading_indicator.dart
│   │   └── error_view.dart
│   └── models/
│       ├── agent.dart
│       ├── message.dart
│       ├── session.dart
│       └── dashboard_data.dart
└── services/
    ├── storage_service.dart    # SQLite + SharedPrefs
    ├── push_service.dart       # FCM handling
    ├── audio_service.dart      # Voice record/play
    └── location_service.dart   # Geolocation
```

---

## 6. ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ

### 6.1 Чат с агентами

| Функция | Описание |
|---------|---------|
| Список агентов | 11 агентов + 2 группы Telegram |
| История | SQLite кэш последних 200 сообщений на агента |
| Стриминг | WebSocket event `session.message` (streaming=true) |
| Markdown | Рендер кода, таблиц, списков |
| Медиа | Отправка фото (camera.snap), файлов |
| Голос | Запись WAV → отправка как attachment |
| TTS | flutter_tts для озвучки ответа агента |
| Offline | Отображение кэша без сети |

### 6.2 Дашборды (нативные, не WebView)

**KPI Dashboard** — данные из агента `ops` / `finance`:
- Выручка дня / месяца
- Количество лидов
- Конверсия
- Статус агентов (online/offline)
- Статус кронов (29 OpenClaw + 13 системных)

**Rituals Dashboard** — из агента `ops` / `main`:
- Список ритуалов на день
- Чекбоксы выполнения
- Время выполнения

**Office Dashboard** — из агента `ops`:
- Посещаемость
- Задачи команды
- Очередь приоритетов

**Automation Dashboard** — из агента `devops`:
- Статус кронов (активен/ошибка/последний запуск)
- Логи последних выполнений
- Алерты Gateway

*Данные дашбордов получаются через chat.send к соответствующему агенту с командой `/status` или специальным API endpoint.*

### 6.3 Push-уведомления

| Триггер | Приоритет | Действие по тапу |
|---------|-----------|-----------------|
| Ответ агента (фон) | Normal | Открыть чат агента |
| Срочная эскалация | High | Открыть чат + звук |
| Алерт крона | Normal | Открыть Notifications |
| Упоминание в группе | High | Открыть группу |

FCM Topics:
- `axis_agents` — все ответы агентов
- `axis_urgent` — только срочные
- `axis_crons` — алерты кронов

### 6.4 Камера

```dart
// Flow: Пользователь → Фото → Агент анализирует
1. Тап на 📷 в чате
2. Camera picker / файл
3. Resize до 1024px max
4. Base64 encode
5. WS: sessions.send с attachment
6. Агент возвращает анализ
```

### 6.5 Голос

**Запись:**
```dart
// Запись: hold кнопку 🎤
record package → WAV 16kHz mono
Max duration: 60 sec
```

**Отправка:**
```dart
// Файл → Base64 → attachment в сообщении
// Агент транскрибирует через OpenAI Whisper
```

**TTS ответ:**
```dart
// Ответ агента → flutter_tts.speak()
// Настройка: скорость, голос, язык (ru)
```

### 6.6 Геолокация

```dart
// Доступ: при запуске (опционально)
// Использование:
- Напоминания по месту (geofencing)
- "Ты в офисе? Начать стендап?"
- Трекинг для агента ops

// Отправка агенту:
"[Геолокация: 51.1801° N, 71.4460° E, Астана]"
```

### 6.7 Файлы

- Фото из галереи/камеры
- PDF, DOCX, XLSX
- Максимум 20 МБ
- Предпросмотр перед отправкой

### 6.8 Офлайн режим

| Данные | Кэш | TTL |
|--------|-----|-----|
| История чата | SQLite | Без ограничений |
| KPI данные | SQLite | 1 час |
| Ритуалы | SQLite | 24 часа |
| Список агентов | SharedPrefs | 7 дней |
| Gateway token | SharedPrefs | Permanent |

---

## 7. НЕФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ

### 7.1 Производительность
- Запуск приложения: < 2 сек до HomeScreen
- Подключение WS: < 3 сек
- Отрисовка списка агентов: < 100ms
- Streaming: первый токен < 500ms

### 7.2 Безопасность
- Token хранится в **FlutterSecureStorage** (не SharedPrefs!)
- Pinning TLS сертификата Gateway (опционально)
- Device keypair в Keychain (iOS) / KeyStore (Android)
- Biometric unlock (Face ID / Fingerprint)

### 7.3 UX
- Поддержка тёмной темы (система)
- Haptic feedback на отправку
- Pull-to-refresh на дашбордах
- Swipe-to-delete уведомлений

---

## 8. ТРЕБОВАНИЯ К СЕРВЕРУ

### 8.1 Gateway конфигурация

```yaml
# Требуется для мобильного приложения:
gateway:
  bind: "0.0.0.0"          # или через Cloudflare Tunnel
  auth:
    token: "YOUR_GATEWAY_TOKEN"
  
  # Device pairing - авто-одобрение мобильного устройства
  devices:
    autoApprove: false      # оператор одобряет через openclaw devices approve
```

### 8.2 FCM Setup

1. Firebase проект: `axis-mobile-app`
2. Android: `google-services.json` → `android/app/`
3. iOS: `GoogleService-Info.plist` → `ios/Runner/`
4. FCM Server Key → в OpenClaw config для push-нотификаций
5. Сервер отправки: OpenClaw кастомный крон или webhook

### 8.3 Cloudflare Tunnel

```bash
# Туннель для внешнего доступа:
cloudflared tunnel create axis-gateway
cloudflared tunnel route dns axis-gateway gateway.axis.company.kz

# Config:
tunnel: <tunnel-id>
credentials-file: ~/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: gateway.axis.company.kz
    service: ws://127.0.0.1:18789
  - service: http_status:404
```

---

## 9. ПЛАН РАЗРАБОТКИ (4 НЕДЕЛИ)

### Неделя 1 — Foundation
**Цель:** Рабочее подключение к Gateway + базовый чат

| День | Задача |
|------|--------|
| 1 | Flutter проект, структура, тема AXIS |
| 2 | GatewayClient: WS + handshake + device identity |
| 3 | Auth: LoginScreen, QR scan, сохранение token |
| 4 | AgentListScreen: список 11 агентов |
| 5 | ChatScreen: отправка/получение, стриминг |

**Deliverable:** Можно общаться с агентом через приложение ✅

### Неделя 2 — Media & Features
**Цель:** Камера, голос, файлы, уведомления

| День | Задача |
|------|--------|
| 1 | FCM push: setup Firebase, обработка фон/форегроунд |
| 2 | Camera: snap + отправка агенту |
| 3 | Voice: запись + TTS воспроизведение |
| 4 | Files: picker, preview, отправка |
| 5 | Geolocation: запрос прав, отправка координат |

**Deliverable:** Полная медиа-интеграция ✅

### Неделя 3 — Dashboards
**Цель:** 4 нативных дашборда с реальными данными

| День | Задача |
|------|--------|
| 1 | DashboardProvider: запросы к агентам, парсинг данных |
| 2 | KPI Dashboard: виджеты, графики |
| 3 | Rituals Dashboard: чеклист, расписание |
| 4 | Office + Automation Dashboards |
| 5 | Pull-to-refresh, кэш, offline mode |

**Deliverable:** Все 4 дашборда работают ✅

### Неделя 4 — Polish & Release
**Цель:** Полировка, тестирование, релиз

| День | Задача |
|------|--------|
| 1 | Offline mode: SQLite кэш всего |
| 2 | Settings: все настройки, biometric |
| 3 | UI polish: анимации, тёмная тема, иконки |
| 4 | Тестирование Android + iOS |
| 5 | Build APK + IPA, документация |

**Deliverable:** Релизные сборки ✅

---

## 10. КРИТИЧЕСКИЕ ЗАВИСИМОСТИ

| Зависимость | Ответственный | Срок |
|-------------|---------------|------|
| Cloudflare Tunnel URL для внешнего доступа | devops | Неделя 1 |
| FCM Server Key + конфиг в Gateway | devops | Неделя 2 |
| Firebase проект (android/ios plist) | devops | Неделя 2 |
| KPI формулы + формат данных от агентов | ops/finance | Неделя 3 |
| Формат ритуалов от ops | ops | Неделя 3 |
| Apple Developer / Play Console аккаунт | main | Неделя 4 |

---

## 11. МЕТРИКИ УСПЕХА

- ✅ Подключение к Gateway за < 3 сек
- ✅ Чат со всеми 11 агентами работает
- ✅ Push-уведомления доставляются в фоне
- ✅ Дашборды обновляются без перезапуска
- ✅ Офлайн: последние 200 сообщений доступны без сети
- ✅ Размер APK < 30 МБ
- ✅ Crash-rate < 0.1%

---

## 12. СЛЕДУЮЩИЕ ШАГИ (после v1.0)

- Trello интеграция в дашборды
- Биометрическая авторизация (Face ID / Fingerprint)
- Apple Watch / Wear OS компаньон
- Виджеты на рабочий стол (KPI виджет)
- Белый лейбл (для клиентов AXIS)

---

*ТЗ составлено: Mobile Developer Agent | AXIS | 2026-03-20*  
*Готово к старту разработки: Неделя 1, День 1*
