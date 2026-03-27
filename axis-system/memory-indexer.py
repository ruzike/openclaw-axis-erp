#!/usr/bin/env python3
"""
AXIS Memory Indexer - Инкрементальная индексация для семантического поиска.
Использует ChromaDB + OpenAI Embeddings.

Использование:
    python3 memory-indexer.py              # Полная индексация
    python3 memory-indexer.py --check      # Проверка статуса без индексации
    python3 memory-indexer.py --rebuild    # Полная перестройка базы
"""
import os
import sys
import json
import glob
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Настройка логирования
LOG_DIR = Path("/tmp/openclaw")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "memory-infra.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Пути
BASE_DIR = Path("/home/axis/openclaw")
CHROMA_DIR = BASE_DIR / "axis-system" / ".chroma-db"
STATE_FILE = BASE_DIR / "axis-system" / ".indexer-state.json"

# Источники для индексации
INDEX_SOURCES = [
    BASE_DIR / "projects-history",
    BASE_DIR / "agents" / "*" / "MEMORY.md",
    BASE_DIR / "agents" / "*" / "knowledge" / "*.md",
    BASE_DIR / "axis-system" / "knowledge" / "*.md",
]

# Размер чанка для индексации (в символах)
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200


def load_env() -> str:
    """Загрузить OPENAI_API_KEY из .env файлов OpenClaw"""
    env_files = [
        Path.home() / ".openclaw" / ".env.user",
        Path.home() / ".openclaw" / ".env",
    ]
    
    for env_file in env_files:
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENAI_API_KEY='):
                        key = line.split('=', 1)[1].strip('"\'')
                        os.environ['OPENAI_API_KEY'] = key
                        return key
    
    # Fallback на переменную окружения
    return os.environ.get('OPENAI_API_KEY', '')


def get_file_hash(filepath: Path) -> str:
    """Получить хеш файла для инкрементальной индексации"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def load_state() -> Dict:
    """Загрузить состояние индексатора"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"indexed_files": {}, "last_run": None}


def save_state(state: Dict):
    """Сохранить состояние индексатора"""
    state["last_run"] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def chunk_text(text: str, source: str) -> List[Dict]:
    """Разбить текст на чанки с метаданными"""
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_len = 0
    current_header = ""
    
    for line in lines:
        # Отслеживаем заголовки для контекста
        if line.startswith('#'):
            current_header = line.strip()
        
        current_chunk.append(line)
        current_len += len(line) + 1
        
        if current_len >= CHUNK_SIZE:
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "source": source,
                "header": current_header,
                "char_count": len(chunk_text)
            })
            # Overlap: оставляем последние N символов
            overlap_lines = []
            overlap_len = 0
            for l in reversed(current_chunk):
                overlap_len += len(l) + 1
                overlap_lines.insert(0, l)
                if overlap_len >= CHUNK_OVERLAP:
                    break
            current_chunk = overlap_lines
            current_len = overlap_len
    
    # Добавляем остаток
    if current_chunk:
        chunk_text = '\n'.join(current_chunk)
        if len(chunk_text.strip()) > 50:  # Игнорируем слишком короткие
            chunks.append({
                "text": chunk_text,
                "source": source,
                "header": current_header,
                "char_count": len(chunk_text)
            })
    
    return chunks


def collect_files() -> List[Path]:
    """Собрать все файлы для индексации"""
    files = []
    
    for pattern in INDEX_SOURCES:
        pattern_str = str(pattern)
        if '*' in pattern_str:
            files.extend([Path(p) for p in glob.glob(pattern_str, recursive=True)])
        else:
            if pattern.is_dir():
                files.extend(pattern.rglob("*.md"))
            elif pattern.exists():
                files.append(pattern)
    
    # Фильтруем
    filtered = []
    for f in files:
        if not f.exists() or not f.is_file():
            continue
        if '_template' in str(f):
            continue
        if '.bak' in str(f):
            continue
        filtered.append(f)
    
    return list(set(filtered))


def index_files(rebuild: bool = False):
    """Основная функция индексации"""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        logger.error("ChromaDB не установлен. Установите: pip install chromadb openai")
        sys.exit(1)
    
    api_key = load_env()
    if not api_key:
        logger.error("OPENAI_API_KEY не найден в ~/.openclaw/.env.user или .env")
        sys.exit(1)
    
    # Инициализация ChromaDB
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Embedding функция через OpenAI
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small"
    )
    
    # Создаём или получаем коллекцию
    if rebuild:
        try:
            client.delete_collection("axis_memory")
            logger.info("🗑️ Старая коллекция удалена")
        except Exception:
            pass
        state = {"indexed_files": {}, "last_run": None}
    else:
        state = load_state()
    
    collection = client.get_or_create_collection(
        name="axis_memory",
        embedding_function=openai_ef,
        metadata={"description": "AXIS Corporate Memory"}
    )
    
    # Собираем файлы
    files = collect_files()
    logger.info(f"📁 Найдено {len(files)} файлов для проверки")
    
    indexed_count = 0
    skipped_count = 0
    total_chunks = 0
    
    for filepath in files:
        file_key = str(filepath.relative_to(BASE_DIR))
        file_hash = get_file_hash(filepath)
        
        # Проверяем, изменился ли файл
        if not rebuild and state["indexed_files"].get(file_key) == file_hash:
            skipped_count += 1
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content.strip()) < 100:
                continue
            
            # Удаляем старые чанки этого файла
            try:
                existing = collection.get(where={"source": file_key})
                if existing["ids"]:
                    collection.delete(ids=existing["ids"])
            except Exception:
                pass
            
            # Создаём чанки
            chunks = chunk_text(content, file_key)
            
            if chunks:
                ids = [f"{file_key}_{i}" for i in range(len(chunks))]
                documents = [c["text"] for c in chunks]
                metadatas = [
                    {
                        "source": c["source"],
                        "header": c["header"][:200] if c["header"] else "",
                        "char_count": c["char_count"]
                    }
                    for c in chunks
                ]
                
                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                
                total_chunks += len(chunks)
                indexed_count += 1
                state["indexed_files"][file_key] = file_hash
                logger.info(f"✅ {file_key}: {len(chunks)} чанков")
        
        except Exception as e:
            logger.error(f"❌ Ошибка при индексации {filepath}: {e}")
    
    save_state(state)
    
    # Статистика
    stats = collection.count()
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 ИТОГИ ИНДЕКСАЦИИ:")
    logger.info(f"   Проиндексировано: {indexed_count} файлов ({total_chunks} чанков)")
    logger.info(f"   Пропущено (без изменений): {skipped_count}")
    logger.info(f"   Всего в базе: {stats} чанков")
    logger.info(f"   База: {CHROMA_DIR}")
    logger.info(f"{'='*50}")
    
    return {"indexed": indexed_count, "skipped": skipped_count, "total": stats}


def check_status():
    """Проверить статус индексатора без индексации"""
    state = load_state()
    
    try:
        import chromadb
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_or_create_collection(name="axis_memory")
        count = collection.count()
    except Exception as e:
        count = 0
        logger.warning(f"Не удалось подключиться к ChromaDB: {e}")
    
    files = collect_files()
    
    print(f"\n{'='*50}")
    print("📊 СТАТУС ИНДЕКСАТОРА AXIS MEMORY")
    print(f"{'='*50}")
    print(f"База данных: {CHROMA_DIR}")
    print(f"Чанков в базе: {count}")
    print(f"Файлов для индексации: {len(files)}")
    print(f"Проиндексировано файлов: {len(state.get('indexed_files', {}))}")
    print(f"Последний запуск: {state.get('last_run', 'никогда')}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if "--check" in args:
        check_status()
    elif "--rebuild" in args:
        logger.info("🔄 Полная перестройка индекса...")
        index_files(rebuild=True)
    elif "--help" in args or "-h" in args:
        print(__doc__)
    else:
        logger.info("🚀 Инкрементальная индексация...")
        index_files(rebuild=False)
