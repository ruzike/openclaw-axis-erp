# TOOLS.md - Mobile Developer

## Flutter CLI
```bash
flutter create axis_app
flutter run -d chrome    # web debug
flutter build apk        # Android release
flutter build ios         # iOS release
```

## OpenClaw Gateway API
```bash
# Проверка статуса
curl http://localhost:3000/api/status

# Отправка сообщения агенту
curl -X POST http://localhost:3000/api/sessions/send \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"sessionKey":"agent:main:...", "message":"текст"}'
```

## Полезные команды
```bash
# Dart analyzer
dart analyze

# Тесты
flutter test

# Генерация иконок
flutter pub run flutter_launcher_icons
```
