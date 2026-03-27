#!/bin/bash
# First remove old Daily MEMORY Update jobs
IDS=$(openclaw cron list | grep "Daily MEMORY Update" | awk '{print $1}')
for ID in $IDS; do
  openclaw cron rm "$ID"
done

# Create new jobs with --no-deliver
AGENTS=$(ls /home/axis/openclaw/agents/)
for AGENT in $AGENTS; do
  if [ -d "/home/axis/openclaw/agents/$AGENT" ]; then
    openclaw cron add --agent "$AGENT" --name "Daily MEMORY Update" --cron "0 23 * * *" --no-deliver --model "google/gemini-3.1-pro-preview" --message "АУДИТ ПАМЯТИ: Проанализируй свои действия за день и обнови свой файл MEMORY.md. Зафиксируй новые задачи, договоренности и прогресс. Обязательно используй append (добавление). Это автоматическое системное задание. Ответь кратким отчетом об успешном обновлении."
  fi
done
