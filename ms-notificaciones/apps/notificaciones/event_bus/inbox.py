"""Registro idempotente de eventos consumidos."""

from __future__ import annotations

import logging

from agm_events.envelope import EventEnvelope

from apps.notificaciones.models import EventInbox

logger = logging.getLogger(__name__)


def try_register_event(envelope: EventEnvelope, handler: str) -> bool:
    """
    Registra event_id en inbox.
    Returns True si es nuevo y debe procesarse; False si duplicado.
    """
    if EventInbox.objects.filter(event_id=envelope.event_id).exists():
        logger.info(
            'inbox_duplicate_discarded',
            extra={
                'event_id': str(envelope.event_id),
                'event_name': envelope.event_name,
                'handler': handler,
            },
        )
        return False
    EventInbox.objects.create(
        event_id=envelope.event_id,
        event_name=envelope.event_name,
        handler=handler,
    )
    logger.info(
        'inbox_registered',
        extra={
            'event_id': str(envelope.event_id),
            'event_name': envelope.event_name,
            'handler': handler,
        },
    )
    return True
