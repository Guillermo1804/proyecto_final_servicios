"""Patron Inbox — deduplicacion por event_id."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from agm_events.exceptions import DuplicateEventError


@dataclass(frozen=True)
class InboxRecord:
    event_id: str
    event_name: str
    processed_at: str
    handler: str


class InboxStore:
    """Registro de eventos ya procesados (idempotencia)."""

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
                CREATE TABLE IF NOT EXISTS event_inbox (
                    event_id TEXT PRIMARY KEY,
                    event_name TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    handler TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def exists(self, event_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM event_inbox WHERE event_id = ?", (event_id,)
            ).fetchone()
        return row is not None

    def register(self, event_id: str, event_name: str, handler: str) -> InboxRecord:
        if self.exists(event_id):
            raise DuplicateEventError(f"event_id already processed: {event_id}")
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO event_inbox (event_id, event_name, processed_at, handler)
                VALUES (?, ?, ?, ?)
                """,
                (event_id, event_name, now, handler),
            )
            conn.commit()
        return InboxRecord(
            event_id=event_id,
            event_name=event_name,
            processed_at=now,
            handler=handler,
        )

    def try_register(self, event_id: str, event_name: str, handler: str) -> bool:
        """
        Registra si no existe.
        Returns True si se registro (procesar), False si es duplicado.
        """
        if self.exists(event_id):
            return False
        self.register(event_id, event_name, handler)
        return True

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM event_inbox").fetchone()
        return int(row["c"]) if row else 0
