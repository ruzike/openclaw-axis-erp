"""
event_queue.py — SQLite буфер для Trello webhook событий

Гарантирует что ни одно событие не потеряется при:
- Крашах Flask
- Временных ошибках обработки
- Перезагрузке сервера

Использование:
    from event_queue import EventQueue
    
    queue = EventQueue()
    event_id = queue.enqueue(payload_dict)
    queue.mark_processed(event_id)
    queue.mark_failed(event_id, error_msg)
    
    # Ретрай неудачных
    for event in queue.get_pending(limit=10):
        process(event)
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from threading import Lock

logger = logging.getLogger(__name__)

# Путь к SQLite файлу
QUEUE_DB = Path("/home/axis/openclaw/axis-system/trello-webhook/event_queue.sqlite")

# Статусы событий
STATUS_PENDING    = "pending"
STATUS_PROCESSING = "processing"
STATUS_DONE       = "done"
STATUS_FAILED     = "failed"

# Максимум попыток обработки
MAX_RETRIES = 3

# Хранить события N дней
RETENTION_DAYS = 7


class EventQueue:
    def __init__(self, db_path: Path = QUEUE_DB):
        self.db_path = db_path
        self._lock = Lock()
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Создаёт таблицу если не существует"""
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    received_at TEXT    NOT NULL,
                    board_id    TEXT,
                    board_name  TEXT,
                    action_type TEXT,
                    payload     TEXT    NOT NULL,
                    status      TEXT    NOT NULL DEFAULT 'pending',
                    attempts    INTEGER NOT NULL DEFAULT 0,
                    last_error  TEXT,
                    processed_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON events(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_received ON events(received_at)")
        logger.info(f"EventQueue инициализирован: {self.db_path}")

    def enqueue(self, payload: dict) -> int:
        """
        Сохраняет событие в очередь.
        Возвращает ID записи.
        """
        # Извлекаем метаданные для удобного просмотра
        action = payload.get("action", {})
        board   = action.get("data", {}).get("board", {})

        board_id   = board.get("id", "")
        board_name = board.get("name", "")
        action_type = action.get("type", "")

        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            with self._conn() as conn:
                cur = conn.execute("""
                    INSERT INTO events
                        (received_at, board_id, board_name, action_type, payload, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (now, board_id, board_name, action_type, json.dumps(payload), STATUS_PENDING))
                event_id = cur.lastrowid

        logger.debug(f"Событие #{event_id} помещено в очередь: {action_type} / {board_name}")
        return event_id

    def mark_processing(self, event_id: int):
        """Отмечает событие как обрабатываемое"""
        with self._conn() as conn:
            conn.execute("""
                UPDATE events
                SET status='processing', attempts=attempts+1
                WHERE id=?
            """, (event_id,))

    def mark_processed(self, event_id: int):
        """Отмечает событие как успешно обработанное"""
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute("""
                UPDATE events
                SET status='done', processed_at=?, last_error=NULL
                WHERE id=?
            """, (now, event_id))
        logger.debug(f"Событие #{event_id} обработано")

    def mark_failed(self, event_id: int, error: str):
        """Отмечает событие как упавшее. При MAX_RETRIES → status=failed"""
        with self._conn() as conn:
            row = conn.execute("SELECT attempts FROM events WHERE id=?", (event_id,)).fetchone()
            attempts = row["attempts"] if row else 0

            if attempts >= MAX_RETRIES:
                conn.execute("""
                    UPDATE events
                    SET status='failed', last_error=?
                    WHERE id=?
                """, (str(error)[:500], event_id))
                logger.warning(f"Событие #{event_id} провалилось после {attempts} попыток: {error}")
            else:
                conn.execute("""
                    UPDATE events
                    SET status='pending', last_error=?
                    WHERE id=?
                """, (str(error)[:500], event_id))
                logger.info(f"Событие #{event_id} вернулось в очередь (попытка {attempts})")

    def get_pending(self, limit: int = 20) -> list:
        """Возвращает события ожидающие обработки"""
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT id, payload, board_name, action_type, attempts
                FROM events
                WHERE status='pending'
                ORDER BY received_at ASC
                LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        """Статистика очереди"""
        with self._conn() as conn:
            stats = {}
            for status in [STATUS_PENDING, STATUS_PROCESSING, STATUS_DONE, STATUS_FAILED]:
                count = conn.execute(
                    "SELECT COUNT(*) FROM events WHERE status=?", (status,)
                ).fetchone()[0]
                stats[status] = count
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            stats["total"] = total
        return stats

    def cleanup_old(self):
        """Удаляет обработанные события старше RETENTION_DAYS дней"""
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
        with self._conn() as conn:
            deleted = conn.execute("""
                DELETE FROM events
                WHERE status='done' AND processed_at < ?
            """, (cutoff,)).rowcount
        if deleted:
            logger.info(f"Очистка: удалено {deleted} старых событий")
        return deleted
