#!/bin/bash
# Загружает последний бэкап на Google Drive
# Запускается после daily-backup.sh

BACKUP_DIR="/home/axis/backups"
GDRIVE_SCRIPT="/home/axis/openclaw/skills/google-drive/scripts/gdrive-upload.py"

# Найти последний бэкап
LATEST=$(ls -t "$BACKUP_DIR"/axis-backup-*.tar.gz 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "❌ Бэкап не найден"
    exit 1
fi

echo "📤 Загружаю на Google Drive: $(basename $LATEST)"
python3 "$GDRIVE_SCRIPT" "$LATEST" --folder-name "AXIS Backups" --account ruslanshakirzhanovich@gmail.com

if [ $? -eq 0 ]; then
    echo "✅ Бэкап загружен на Google Drive"
else
    echo "❌ Ошибка загрузки на Google Drive"
    exit 1
fi
