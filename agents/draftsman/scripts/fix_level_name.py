#!/usr/bin/env python3
"""
Заменить имя уровня в revit_commands.jsonl.
"""
import json
import sys

INPUT_FILE = '/home/axis/openclaw/agents/draftsman/temp/revit_commands.jsonl'
OUTPUT_FILE = '/mnt/c/bridge/revit_commands.jsonl'

if len(sys.argv) < 2:
    print("Usage: python3 fix_level_name.py '<имя уровня>'")
    print("Пример: python3 fix_level_name.py 'Level 1'")
    sys.exit(1)

new_level_name = sys.argv[1]

commands = []
with open(INPUT_FILE) as f:
    for line in f:
        cmd = json.loads(line.strip())
        cmd['level'] = new_level_name
        commands.append(cmd)

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for cmd in commands:
        f.write(json.dumps(cmd, ensure_ascii=False) + '\n')

print(f"✅ Обновлено {len(commands)} команд")
print(f"Новое имя уровня: '{new_level_name}'")
print(f"Файл: {OUTPUT_FILE}")
