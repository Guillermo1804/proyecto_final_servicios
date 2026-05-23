"""Escritura transaccional en event_outbox."""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from django.conf import settings
from django.db import transaction

from agm_events.envelope import build_envelope

from apps.core.event_bus.context import get_causation_id, get_correlation_id
from apps.core.models import EventOutbox

logger = logging.getLogger(__name__)


def _event_version(event_name: str) -> int:
    if ".v" in event_name:
        try:
            return int(event_name.rsplit(".v", 1)[-1])
        except ValueError:
            pass
    return 1


def enqueue_domain_event(
    *,
    event_name: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    causation_id: str | None = None,
) -> None:
    """
    Registra un evento en outbox tras commit exitoso de la transaccion actual.
    No publica a RabbitMQ (lo hace run_event_outbox).
    """
    if not getattr(settings, "USE_EVENT_BUS", False):
        return

    correlation_id = get_correlation_id()
    cause = causation_id or get_causation_id() or correlation_id
    event_id = str(uuid4())
    version = _event_version(event_name)

    envelope = build_envelope(
        event_id=event_id,
        event_name=event_name,
        event_version=version,
        aggregate_type=aggregate_type,
        aggregate_id=str(aggregate_id),
        source_service=getattr(settings, "SERVICE_NAME", "ms-auth"),
        payload=payload,
        correlation_id=correlation_id,
        causation_id=cause,
    )

    stored_payload = {
        **payload,
        "_agm_meta": {
            "correlation_id": correlation_id,
            "causation_id": cause,
        },
    }

    def _persist() -> None:
        from uuid import UUID

        EventOutbox.objects.create(
            event_id=UUID(envelope.event_id),
            event_name=envelope.event_name,
            event_version=envelope.event_version,
            aggregate_type=envelope.aggregate_type,
            aggregate_id=envelope.aggregate_id,
            payload=stored_payload,
            status=EventOutbox.Status.PENDING,
        )
        logger.info(
            "outbox_enqueued",
            extra={
                "event_id": envelope.event_id,
                "correlation_id": correlation_id,
                "event_name": event_name,
            },
        )

    transaction.on_commit(_persist)
