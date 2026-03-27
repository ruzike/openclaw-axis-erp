#!/usr/bin/env python3
"""
AXIS Memory Auto-Compaction
Сжимает MEMORY.md агентов: оставляет "вечнозелёные" факты + последние 7 дней.
Старые записи архивируются в memory/archive/.
Запускается по cron раз в неделю (воскресенье).
"""
import os
import re
import shutil
from pathlib import Path
from datetime import datetime, timedelta

AGENTS_DIR = Path("/home/axis/openclaw/agents")
MAX_LINES = 300  # Если MEMORY.md больше — сжимаем
KEEP_DAYS = 7    # Оставляем записи за последние N дней

def compact_agent(agent_name):
    memory_file = AGENTS_DIR / agent_name / "MEMORY.md"
    if not memory_file.exists():
        return f"⏭️ {agent_name}: нет MEMORY.md"
    
    lines = memory_file.read_text(encoding='utf-8').splitlines()
    line_count = len(lines)
    
    if line_count <= MAX_LINES:
        return f"✅ {agent_name}: {line_count} строк (норма, пропускаем)"
    
    # Создаём архив
    archive_dir = AGENTS_DIR / agent_name / "memory" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Бэкап
    timestamp = datetime.now().strftime("%Y-%m-%d")
    backup = archive_dir / f"MEMORY-{timestamp}.md"
    shutil.copy2(memory_file, backup)
    
    # Разделяем на секции по "## " заголовкам
    content = memory_file.read_text(encoding='utf-8')
    sections = re.split(r'(?=^## )', content, flags=re.MULTILINE)
    
    # Фильтруем: оставляем заголовок + секции с датами за последние KEEP_DAYS дней
    cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
    kept = []
    archived = []
    
    for section in sections:
        # Ищем дату в секции (формат YYYY-MM-DD)
        date_match = re.search(r'20\d{2}-\d{2}-\d{2}', section)
        if date_match:
            try:
                section_date = datetime.strptime(date_match.group(), "%Y-%m-%d")
                if section_date >= cutoff:
                    kept.append(section)
                else:
                    archived.append(section)
                continue
            except ValueError:
                pass
        
        # Секции без дат (вечнозелёные) — оставляем
        if section.strip():
            kept.append(section)
    
    # Записываем сжатый MEMORY.md
    new_content = "".join(kept)
    memory_file.write_text(new_content, encoding='utf-8')
    
    new_lines = len(new_content.splitlines())
    archived_count = len(archived)
    
    return f"🗜️ {agent_name}: {line_count} → {new_lines} строк (архивировано {archived_count} секций в {backup.name})"

def main():
    print(f"🧹 AXIS Memory Compaction — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    agents = [d.name for d in AGENTS_DIR.iterdir() if d.is_dir() and (d / "SOUL.md").exists()]
    
    for agent in sorted(agents):
        result = compact_agent(agent)
        print(result)
    
    print("=" * 60)
    print("✅ Compaction завершён")

if __name__ == "__main__":
    main()
