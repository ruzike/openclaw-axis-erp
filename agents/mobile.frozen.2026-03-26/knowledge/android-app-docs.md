# Android App (Node) — Official Docs

## Ключевые моменты:
- Исходники: github.com/openclaw/openclaw → apps/android
- Сборка: Java 17 + Android SDK → ./gradlew :app:assemblePlayDebug
- Подключение: WebSocket к Gateway (ws://host:18789)
- Device pairing: openclaw devices approve <requestId>
- Foreground service для постоянного подключения

## Команды Android Node:
- chat.history, chat.send, chat.subscribe
- canvas.eval, canvas.snapshot, canvas.navigate
- camera.snap (jpg), camera.clip (mp4)
- device.status, device.info, device.permissions, device.health
- notifications.list, notifications.actions
- photos.latest
- contacts.search, contacts.add
- calendar.events, calendar.add
- callLog.search, sms.search
- motion.activity, motion.pedometer

## Voice:
- Mic on/off в Voice tab
- TTS playback (ElevenLabs или system TTS)
- Transcript capture

## Canvas:
- Gateway Canvas Host: http://host:18789/__openclaw__/canvas/
- A2UI: http://host:18789/__openclaw__/a2ui/
- Live-reload на файловые изменения
