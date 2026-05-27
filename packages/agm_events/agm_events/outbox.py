"""Patron Transactional Outbox — almacen SQLite para humo y referencia Django."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class OutboxStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass(frozen=True)
class OutboxRecord:
    id: int
    event_id: str
    event_name: str
    payload_json: str
    status: OutboxStatus
    created_at: str
    published_at: str | None
    retry_count: int
    last_error: str | None


class OutboxStore:
    """Persistencia outbox (SQLite). En MS Django sera tabla MySQL equivalente."""

    def __init__(self, db_path: Path | str) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    event_name TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    published_at TEXT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_outbox_status_created "
                "ON event_outbox (status, created_at)"
            )
            conn.commit()

    def insert_pending(self, event_id: str, event_name: str, envelope_dict: dict[str, Any]) -> int:
        now = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(envelope_dict, ensure_ascii=False)
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO event_outbox (event_id, event_name, payload_json, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_id, event_name, payload_json, OutboxStatus.PENDING.value, now),
            )
            conn.commit()
            return int(cur.lastrowid)

    def list_pending(self) -> list[OutboxRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM event_outbox WHERE status = ? ORDER BY created_at ASC",
                (OutboxStatus.PENDING.value,),
            ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def mark_published(self, event_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE event_outbox
                SET status = ?, published_at = ?, last_error = NULL
                WHERE event_id = ?
                """,
                (OutboxStatus.PUBLISHED.value, now, event_id),
            )
            conn.commit()

    def mark_failed(self, event_id: str, error: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE event_outbox
                SET status = ?, retry_count = retry_count + 1, last_error = ?
                WHERE event_id = ?
                """,
                (OutboxStatus.FAILED.value, error[:2000], event_id),
            )
            conn.commit()

    def get(self, event_id: str) -> OutboxRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM event_outbox WHERE event_id = ?", (event_id,)
            ).fetchone()
        return self._row_to_record(row) if row else None

    def count_by_status(self, status: OutboxStatus) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM event_outbox WHERE status = ?", (status.value,)
            ).fetchone()
        return int(row["c"]) if row else 0

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> OutboxRecord:
        return OutboxRecord(
            id=int(row["id"]),
            event_id=str(row["event_id"]),
            event_name=str(row["event_name"]),
            payload_json=str(row["payload_json"]),
            status=OutboxStatus(str(row["status"])),
            created_at=str(row["created_at"]),
            published_at=str(row["published_at"]) if row["published_at"] else None,
            retry_count=int(row["retry_count"]),
            last_error=str(row["last_error"]) if row["last_error"] else None,
        )
