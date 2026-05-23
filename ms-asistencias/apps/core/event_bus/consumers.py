"""Handlers idempotentes para proyecciones MS-5."""

from __future__ import annotations

import logging

from agm_events.envelope import EventEnvelope
from agm_events.validation import validate_full_event

from apps.core.event_bus import projection_service as proj
from apps.core.event_bus.inbox import try_register_event

logger = logging.getLogger(__name__)


def _consume(envelope: EventEnvelope, handler: str, fn) -> None:
    logger.info(
        'event_received',
        extra={
            'event_id': str(envelope.event_id),
            'event_name': envelope.event_name,
            'handler': handler,
        },
    )
    validate_full_event(envelope)
    if not try_register_event(envelope, handler):
        return
    fn(envelope.payload)
    logger.info(
        'projection_updated',
        extra={'event_id': str(envelope.event_id), 'handler': handler},
    )


def handle_periodo_created(envelope: EventEnvelope) -> None:
    _consume(envelope, 'periodo_created', lambda p: proj.upsert_periodo(p))


def handle_periodo_updated(envelope: EventEnvelope) -> None:
    _consume(envelope, 'periodo_updated', lambda p: proj.upsert_periodo(p))


def handle_periodo_closed(envelope: EventEnvelope) -> None:
    _consume(envelope, 'periodo_closed', lambda p: proj.upsert_periodo(p, activo=False))


def handle_materia_created(envelope: EventEnvelope) -> None:
    _consume(envelope, 'materia_created', proj.upsert_materia)


def handle_materia_updated(envelope: EventEnvelope) -> None:
    _consume(envelope, 'materia_updated', proj.upsert_materia)


def handle_materia_closed(envelope: EventEnvelope) -> None:
    _consume(envelope, 'materia_closed', proj.mark_materia_closed)


def handle_alumno_imported(envelope: EventEnvelope) -> None:
    _consume(envelope, 'alumno_imported', proj.handle_alumno_imported)


def handle_alumno_updated(envelope: EventEnvelope) -> None:
    _consume(envelope, 'alumno_updated', proj.handle_alumno_updated)


def handle_alumno_withdrawn(envelope: EventEnvelope) -> None:
    _consume(envelope, 'alumno_withdrawn', proj.handle_alumno_withdrawn)


HANDLERS = {
    'periodo.created.v1': handle_periodo_created,
    'periodo.updated.v1': handle_periodo_updated,
    'periodo.closed.v1': handle_periodo_closed,
    'materia.created.v1': handle_materia_created,
    'materia.updated.v1': handle_materia_updated,
    'materia.closed.v1': handle_materia_closed,
    'alumno.imported.v1': handle_alumno_imported,
    'alumno.updated.v1': handle_alumno_updated,
    'alumno.withdrawn.v1': handle_alumno_withdrawn,
}
