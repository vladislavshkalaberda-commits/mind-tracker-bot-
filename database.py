import sqlite3
from datetime import datetime, date
from typing import List, Dict


class Database:
    def __init__(self, db_path: str = "mind_tracker.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    chat_id TEXT PRIMARY KEY,
                    registered_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT,
                    timestamp TEXT,
                    q1 TEXT,
                    q2 TEXT,
                    q3 TEXT,
                    note TEXT
                )
            """)
            # Migration: add note column if missing (for existing DBs)
            try:
                conn.execute("ALTER TABLE responses ADD COLUMN note TEXT")
            except sqlite3.OperationalError:
                pass
            conn.commit()

    def register_user(self, chat_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (chat_id, registered_at) VALUES (?, ?)",
                (chat_id, datetime.now().isoformat())
            )
            conn.commit()

    def save_response(self, chat_id: str, answers: Dict, timestamp: str, note: str = ""):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO responses (chat_id, timestamp, q1, q2, q3, note)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                chat_id,
                timestamp,
                answers.get("q1", ""),
                answers.get("q2", ""),
                answers.get("q3", ""),
                note,
            ))
            conn.commit()

    def get_responses_today(self, chat_id: str) -> List[Dict]:
        today = date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM responses
                WHERE chat_id = ? AND timestamp LIKE ?
                ORDER BY timestamp ASC
            """, (chat_id, f"{today}%")).fetchall()
        return [dict(r) for r in rows]

    def get_responses_last_days(self, chat_id: str, days: int = 7) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM responses
                WHERE chat_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (chat_id, days * 30)).fetchall()
        return [dict(r) for r in rows]

    def get_total_count(self, chat_id: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM responses WHERE chat_id = ?", (chat_id,)
            ).fetchone()
        return row[0] if row else 0
