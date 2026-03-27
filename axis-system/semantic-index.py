#!/usr/bin/env python3
"""
Семантический индексатор для projects-history/.
Сканирует markdown-файлы, генерирует embeddings через OpenAI,
сохраняет в ChromaDB для семантического поиска.

Использование:
    python3 semantic-index.py              # Инкрементальная индексация
    python3 semantic-index.py --rebuild    # Полная переиндексация
    python3 semantic-index.py --check      # Проверить статус базы
"""
import os
import sys
import glob
import hashlib
import logging
import argparse
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.config import Settings
from openai import OpenAI

# === КОНФИГУРАЦИЯ ===
HISTORY_DIR = "/home/axis/openclaw/projects-history"
CHROMA_DIR = "/home/axis/openclaw/axis-system/.chroma-db"
COLLECTION_NAME = "projects_history"
EMBEDDING_MODEL = "text-embedding-ada-002"
CHUNK_SIZE = 1500  # символов на чанк
CHUNK_OVERLAP = 200  # перекрытие между чанками

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_file_hash(filepath: str) -> str:
    """Вычисляет MD5 хеш содержимого файла."""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """Разбивает текст на чанки с перекрытием."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Пытаемся закончить на границе параграфа или предложения
        if end < len(text):
            # Ищем конец параграфа
            para_end = chunk.rfind('\n\n')
            if para_end > chunk_size * 0.5:
                chunk = chunk[:para_end]
            else:
                # Ищем конец предложения
                for sep in ['. ', '.\n', '! ', '? ']:
                    sent_end = chunk.rfind(sep)
                    if sent_end > chunk_size * 0.5:
                        chunk = chunk[:sent_end + 1]
                        break
        
        if chunk.strip():
            chunks.append(chunk.strip())
        
        start = start + len(chunk) - overlap
        if start <= 0:
            start = end - overlap
    
    return chunks

def extract_title(content: str) -> str:
    """Извлекает заголовок из markdown-файла."""
    lines = content.split('\n')
    for line in lines[:5]:
        if line.startswith('# '):
            return line[2:].strip()
    return "Без названия"

def get_embeddings(client: OpenAI, texts: list) -> list:
    """Получает embeddings для списка текстов через OpenAI API."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"Ошибка получения embeddings: {e}")
        raise

def init_chroma():
    """Инициализирует ChromaDB клиент."""
    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client

def get_indexed_files(collection) -> dict:
    """Возвращает словарь {filepath: hash} уже проиндексированных файлов."""
    try:
        results = collection.get(include=['metadatas'])
        indexed = {}
        for meta in results.get('metadatas', []):
            if meta and 'filepath' in meta and 'file_hash' in meta:
                indexed[meta['filepath']] = meta['file_hash']
        return indexed
    except Exception:
        return {}

def index_file(openai_client: OpenAI, collection, filepath: str, file_hash: str):
    """Индексирует один файл: разбивает на чанки, получает embeddings, сохраняет."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            logger.warning(f"Пустой файл: {filepath}")
            return 0
        
        title = extract_title(content)
        chunks = chunk_text(content)
        
        if not chunks:
            logger.warning(f"Нет чанков для: {filepath}")
            return 0
        
        # Получаем embeddings для всех чанков
        embeddings = get_embeddings(openai_client, chunks)
        
        # Подготавливаем данные для ChromaDB
        ids = [f"{file_hash}_{i}" for i in range(len(chunks))]
        metadatas = [{
            'filepath': filepath,
            'file_hash': file_hash,
            'title': title,
            'chunk_index': i,
            'total_chunks': len(chunks),
            'indexed_at': datetime.now().isoformat()
        } for i in range(len(chunks))]
        
        # Добавляем в коллекцию
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        logger.info(f"✓ {filepath} ({len(chunks)} чанков)")
        return len(chunks)
        
    except Exception as e:
        logger.error(f"✗ Ошибка индексации {filepath}: {e}")
        return 0

def remove_file_from_index(collection, filepath: str):
    """Удаляет файл из индекса."""
    try:
        results = collection.get(where={'filepath': filepath})
        if results['ids']:
            collection.delete(ids=results['ids'])
            logger.info(f"Удалён из индекса: {filepath}")
    except Exception as e:
        logger.error(f"Ошибка удаления {filepath}: {e}")

def run_indexing(rebuild: bool = False):
    """Основной процесс индексации."""
    logger.info("=" * 50)
    logger.info("Семантический индексатор projects-history")
    logger.info("=" * 50)
    
    # Инициализация
    chroma_client = init_chroma()
    openai_client = OpenAI()
    
    # Получаем или создаём коллекцию
    if rebuild:
        logger.info("Режим полной переиндексации...")
        try:
            chroma_client.delete_collection(COLLECTION_NAME)
        except:
            pass
    
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "AXIS projects history semantic search"}
    )
    
    # Получаем уже проиндексированные файлы
    indexed_files = {} if rebuild else get_indexed_files(collection)
    logger.info(f"В индексе: {len(indexed_files)} файлов")
    
    # Сканируем директорию
    all_files = glob.glob(f"{HISTORY_DIR}/**/*.md", recursive=True)
    all_files = [f for f in all_files if '_template' not in f]
    logger.info(f"Найдено файлов: {len(all_files)}")
    
    # Определяем что нужно переиндексировать
    stats = {'added': 0, 'updated': 0, 'skipped': 0, 'removed': 0, 'chunks': 0}
    
    current_files = set()
    for filepath in all_files:
        current_files.add(filepath)
        file_hash = get_file_hash(filepath)
        
        if filepath in indexed_files:
            if indexed_files[filepath] == file_hash:
                stats['skipped'] += 1
                continue
            else:
                # Файл изменён - удаляем старые чанки
                remove_file_from_index(collection, filepath)
                stats['updated'] += 1
        else:
            stats['added'] += 1
        
        chunks_count = index_file(openai_client, collection, filepath, file_hash)
        stats['chunks'] += chunks_count
    
    # Удаляем файлы которых больше нет
    for filepath in indexed_files:
        if filepath not in current_files:
            remove_file_from_index(collection, filepath)
            stats['removed'] += 1
    
    # Итоги
    logger.info("-" * 50)
    logger.info("Индексация завершена:")
    logger.info(f"  Добавлено:    {stats['added']}")
    logger.info(f"  Обновлено:    {stats['updated']}")
    logger.info(f"  Пропущено:    {stats['skipped']}")
    logger.info(f"  Удалено:      {stats['removed']}")
    logger.info(f"  Всего чанков: {stats['chunks']}")
    
    return stats

def check_status():
    """Показывает статус индекса."""
    print("=" * 50)
    print("Статус семантического индекса")
    print("=" * 50)
    
    if not Path(CHROMA_DIR).exists():
        print("❌ База данных не найдена")
        print(f"   Путь: {CHROMA_DIR}")
        print("   Запустите: python3 semantic-index.py")
        return
    
    try:
        chroma_client = init_chroma()
        collection = chroma_client.get_collection(COLLECTION_NAME)
        count = collection.count()
        
        # Получаем уникальные файлы
        results = collection.get(include=['metadatas'])
        files = set()
        for meta in results.get('metadatas', []):
            if meta and 'filepath' in meta:
                files.add(meta['filepath'])
        
        print(f"✓ База данных активна")
        print(f"  Путь: {CHROMA_DIR}")
        print(f"  Коллекция: {COLLECTION_NAME}")
        print(f"  Файлов в индексе: {len(files)}")
        print(f"  Всего чанков: {count}")
        
        # Проверяем файлы на диске
        all_files = glob.glob(f"{HISTORY_DIR}/**/*.md", recursive=True)
        all_files = [f for f in all_files if '_template' not in f]
        print(f"  Файлов на диске: {len(all_files)}")
        
        if len(files) < len(all_files):
            print(f"\n⚠️  Требуется индексация {len(all_files) - len(files)} новых файлов")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    parser = argparse.ArgumentParser(description='Семантический индексатор projects-history')
    parser.add_argument('--rebuild', action='store_true', help='Полная переиндексация')
    parser.add_argument('--check', action='store_true', help='Проверить статус базы')
    args = parser.parse_args()
    
    if args.check:
        check_status()
    else:
        run_indexing(rebuild=args.rebuild)

if __name__ == "__main__":
    main()
