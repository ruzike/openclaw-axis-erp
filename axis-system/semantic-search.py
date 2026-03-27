#!/usr/bin/env python3
"""
Семантический поиск по projects-history/.
Находит релевантные документы по смыслу, а не только по точному совпадению слов.

Использование:
    python3 semantic-search.py "запрос"              # Топ-5 результатов
    python3 semantic-search.py "запрос" --top 10    # Топ-10 результатов
    python3 semantic-search.py "запрос" --verbose   # С отладочной информацией
    python3 semantic-search.py "запрос" --grep      # Fallback на grep-поиск
"""
import os
import sys
import glob
import argparse
import logging
from pathlib import Path

import chromadb
from openai import OpenAI

# === КОНФИГУРАЦИЯ ===
HISTORY_DIR = "/home/axis/openclaw/projects-history"
CHROMA_DIR = "/home/axis/openclaw/axis-system/.chroma-db"
COLLECTION_NAME = "projects_history"
EMBEDDING_MODEL = "text-embedding-ada-002"
DEFAULT_TOP_K = 5
MIN_SIMILARITY = 0.3  # Минимальный порог релевантности

# Настройка логирования
logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def get_query_embedding(client: OpenAI, query: str) -> list:
    """Получает embedding для поискового запроса."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    )
    return response.data[0].embedding

def grep_search(query: str) -> str:
    """Fallback: простой текстовый поиск (как в оригинальном search-projects.py)."""
    query_lower = query.lower()
    results = []
    
    files = glob.glob(f"{HISTORY_DIR}/**/*.md", recursive=True)
    
    for file_path in files:
        if "_template" in file_path:
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if query_lower in content.lower():
                title = content.split('\n')[0].replace('# ', '')
                lines = content.lower().split('\n')
                snippet = ""
                for i, line in enumerate(lines):
                    if query_lower in line:
                        orig_line = content.split('\n')[i]
                        snippet = orig_line.strip()[:100]
                        break
                        
                results.append(f"📄 **{title}**\n   Сниппет: \"...{snippet}...\"\n   Файл: {file_path}")
                
    if not results:
        return f"По запросу '{query}' ничего не найдено (grep-режим)."
        
    return f"🔍 Результаты grep-поиска по запросу '{query}':\n\n" + "\n\n".join(results)

def semantic_search(query: str, top_k: int = DEFAULT_TOP_K, verbose: bool = False) -> str:
    """Семантический поиск по индексу."""
    
    # Проверяем наличие базы
    if not Path(CHROMA_DIR).exists():
        return ("❌ Семантический индекс не найден.\n"
                "   Запустите: python3 /home/axis/openclaw/axis-system/semantic-index.py\n"
                "   Или используйте --grep для текстового поиска.")
    
    try:
        # Инициализация клиентов
        chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        openai_client = OpenAI()
        
        # Получаем коллекцию
        try:
            collection = chroma_client.get_collection(COLLECTION_NAME)
        except Exception:
            return ("❌ Коллекция не найдена. Запустите индексацию:\n"
                    "   python3 /home/axis/openclaw/axis-system/semantic-index.py")
        
        if collection.count() == 0:
            return ("⚠️ Индекс пуст. Добавьте файлы в projects-history/ и запустите:\n"
                    "   python3 /home/axis/openclaw/axis-system/semantic-index.py")
        
        # Получаем embedding для запроса
        if verbose:
            print(f"[DEBUG] Генерация embedding для: '{query}'")
        
        query_embedding = get_query_embedding(openai_client, query)
        
        # Поиск
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k * 2, collection.count()),  # Берём с запасом для фильтрации
            include=['documents', 'metadatas', 'distances']
        )
        
        if verbose:
            print(f"[DEBUG] Найдено кандидатов: {len(results['ids'][0])}")
        
        # Форматируем результаты
        output_parts = []
        seen_files = {}  # filepath -> best_score для дедупликации
        
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            # ChromaDB возвращает L2 distance, конвертируем в similarity
            # Для cosine distance: similarity = 1 - distance (примерно)
            similarity = max(0, 1 - distance / 2)
            
            if similarity < MIN_SIMILARITY:
                continue
            
            filepath = meta.get('filepath', 'Unknown')
            title = meta.get('title', 'Без названия')
            
            # Дедупликация: показываем только лучший чанк из каждого файла
            if filepath in seen_files:
                if similarity <= seen_files[filepath]:
                    continue
            seen_files[filepath] = similarity
            
            # Форматируем сниппет
            snippet = doc[:200].replace('\n', ' ').strip()
            if len(doc) > 200:
                snippet += "..."
            
            score_bar = "█" * int(similarity * 10) + "░" * (10 - int(similarity * 10))
            
            output_parts.append({
                'filepath': filepath,
                'title': title,
                'snippet': snippet,
                'similarity': similarity,
                'score_bar': score_bar
            })
        
        # Сортируем и ограничиваем
        output_parts.sort(key=lambda x: x['similarity'], reverse=True)
        output_parts = output_parts[:top_k]
        
        if not output_parts:
            return (f"🔍 По запросу '{query}' не найдено релевантных результатов.\n"
                    f"   Попробуйте: --grep для текстового поиска")
        
        # Формируем вывод
        header = f"🔍 Семантический поиск: '{query}'\n"
        header += f"   Найдено: {len(output_parts)} релевантных документов\n"
        header += "=" * 60 + "\n"
        
        items = []
        for i, item in enumerate(output_parts, 1):
            rel_path = item['filepath'].replace(HISTORY_DIR + '/', '')
            entry = (
                f"\n{i}. 📄 **{item['title']}**\n"
                f"   Релевантность: [{item['score_bar']}] {item['similarity']:.0%}\n"
                f"   Сниппет: \"{item['snippet']}\"\n"
                f"   Файл: {rel_path}"
            )
            items.append(entry)
        
        return header + "\n".join(items)
        
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        return f"❌ Ошибка семантического поиска: {e}\n   Попробуйте --grep для fallback"

def main():
    parser = argparse.ArgumentParser(
        description='Семантический поиск по projects-history',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  semantic-search.py "ресторан"           # Найдёт также: кафе, бар, общепит
  semantic-search.py "смета проекта"      # Найдёт также: бюджет, оценка, расчёт
  semantic-search.py "проблемы с клиентом" --top 10
  semantic-search.py "рендер интерьера" --verbose
        """
    )
    parser.add_argument('query', nargs='?', help='Поисковый запрос')
    parser.add_argument('--top', type=int, default=DEFAULT_TOP_K, 
                        help=f'Количество результатов (по умолчанию: {DEFAULT_TOP_K})')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Показать отладочную информацию')
    parser.add_argument('--grep', action='store_true',
                        help='Использовать простой текстовый поиск (fallback)')
    
    args = parser.parse_args()
    
    if not args.query:
        parser.print_help()
        sys.exit(1)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.grep:
        print(grep_search(args.query))
    else:
        print(semantic_search(args.query, top_k=args.top, verbose=args.verbose))

if __name__ == "__main__":
    main()
