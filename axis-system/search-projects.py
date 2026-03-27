#!/usr/bin/env python3
"""
Утилита поиска по корпоративной истории AXIS.
Использование: python3 search-projects.py "запрос"
"""
import sys
import os
import glob

HISTORY_DIR = "/home/axis/openclaw/projects-history"

def search(query):
    query = query.lower()
    results = []
    
    # Ищем все md файлы в истории (исключая шаблон)
    files = glob.glob(f"{HISTORY_DIR}/**/*.md", recursive=True)
    
    for file_path in files:
        if "_template" in file_path:
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if query in content.lower():
                # Извлекаем заголовок (первую строку)
                title = content.split('\n')[0].replace('# ', '')
                # Ищем кусок текста с совпадением для сниппета
                lines = content.lower().split('\n')
                snippet = ""
                for i, line in enumerate(lines):
                    if query in line:
                        orig_line = content.split('\n')[i]
                        snippet = orig_line.strip()
                        break
                        
                results.append(f"📄 **{title}**\n   Сниппет: \"...{snippet}...\"\n   Файл: {file_path}\n")
                
    if not results:
        return f"По запросу '{query}' ничего не найдено в архиве проектов."
        
    return f"🔍 Результаты поиска по запросу '{query}':\n\n" + "\n".join(results)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ошибка: укажите поисковый запрос.")
        sys.exit(1)
    print(search(" ".join(sys.argv[1:])))
