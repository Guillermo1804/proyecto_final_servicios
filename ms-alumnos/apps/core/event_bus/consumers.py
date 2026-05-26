"""Handlers del consumidor MS-3."""

from __future__ import annotations

import logging

from agm_events.envelope import EventEnvelope
from agm_events.validation import validate_full_event

from apps.core.event_bus import projection_service as proj
from apps.core.event_bus.inbox import try_register_event

logger = logging.getLogger(__name__)


def _consume(envelope: EventEnvelope, handler: str, fn) -> None:
    validate_full_event(envelope)
    if not try_register_event(envelope, handler):
        return
    fn(envelope.payload)
    logger.info(
        "projection_updated",
        extra={"event_id": str(envelope.event_id), "handler": handler},
    )


def handle_token_revoked(envelope: EventEnvelope) -> None:
    from agm_events.token_revoked import handle_token_revoked as _apply

    _apply(envelope)


def handle_materia_created(envelope: EventEnvelope) -> None:
    _consume(envelope, "materia_created", proj.upsert_materia)


def handle_materia_updated(envelope: EventEnvelope) -> None:
    _consume(envelope, "materia_updated", proj.upsert_materia)


def handle_materia_assigned_teacher(envelope: EventEnvelope) -> None:
    _consume(envelope, "materia_assigned_teacher", proj.assign_teacher)


HANDLERS = {
    "token.revoked.v1": handle_token_revoked,
    "materia.created.v1": handle_materia_created,
    "materia.updated.v1": handle_materia_updated,
    "materia.assigned_teacher.v1": handle_materia_assigned_teacher,
}
