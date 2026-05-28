"""Construccion y serializacion del sobre de evento."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class EventEnvelope:
    event_id: str
    event_name: str
    event_version: int
    aggregate_type: str
    aggregate_id: str
    source_service: str
    correlation_id: str
    causation_id: str
    occurred_at: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json_bytes(self) -> bytes:
        return json.dumps(self.to_dict(), ensure_ascii=False).encode("utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventEnvelope:
        return cls(
            event_id=str(data["event_id"]),
            event_name=str(data["event_name"]),
            event_version=int(data["event_version"]),
            aggregate_type=str(data["aggregate_type"]),
            aggregate_id=str(data["aggregate_id"]),
            source_service=str(data["source_service"]),
            correlation_id=str(data["correlation_id"]),
            causation_id=str(data["causation_id"]),
            occurred_at=str(data["occurred_at"]),
            payload=dict(data.get("payload") or {}),
        )

    @classmethod
    def from_json_bytes(cls, body: bytes) -> EventEnvelope:
        data = json.loads(body.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Envelope JSON must be an object")
        return cls.from_dict(data)


def build_envelope(
    *,
    event_name: str,
    event_version: int,
    aggregate_type: str,
    aggregate_id: str,
    source_service: str,
    payload: dict[str, Any] | None = None,
    event_id: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    occurred_at: str | None = None,
) -> EventEnvelope:
    """Crea un sobre con UUIDs autogenerados si no se proveen."""
    eid = event_id or str(uuid.uuid4())
    cid = correlation_id or eid
    cause = causation_id or cid
    return EventEnvelope(
        event_id=eid,
        event_name=event_name,
        event_version=event_version,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        source_service=source_service,
        correlation_id=cid,
        causation_id=cause,
        occurred_at=occurred_at or _utc_now_iso(),
        payload=payload or {},
    )
