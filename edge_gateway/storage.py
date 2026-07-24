"""SQLite offline buffer for telemetry awaiting delivery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3
from typing import Iterable


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS offline_buffer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    topic TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);
"""


@dataclass(slots=True)
class BufferedMessage:
    id: int
    created_at: str
    topic: str
    payload: dict
    status: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "BufferedMessage":
        return cls(
            id=row["id"],
            created_at=row["created_at"],
            topic=row["topic"],
            payload=json.loads(row["payload"]),
            status=row["status"],
        )


class SQLiteOfflineBuffer:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.execute(SCHEMA_SQL)
            connection.commit()

    def enqueue(self, *, created_at: str, topic: str, payload: dict) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO offline_buffer (created_at, topic, payload, status) VALUES (?, ?, ?, 'pending')",
                (created_at, topic, json.dumps(payload, separators=(",", ":"))),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_pending(self) -> list[BufferedMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, created_at, topic, payload, status FROM offline_buffer WHERE status = 'pending' ORDER BY id"
            ).fetchall()
        return [BufferedMessage.from_row(row) for row in rows]

    def mark_sent(self, message_id: int) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE offline_buffer SET status = 'sent' WHERE id = ?", (message_id,))
            connection.commit()

