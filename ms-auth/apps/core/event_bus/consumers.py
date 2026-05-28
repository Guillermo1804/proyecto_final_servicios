"""Handlers de eventos consumidos por MS-1."""

from __future__ import annotations

import logging

from agm_events.envelope import EventEnvelope

from apps.core.event_bus.context import set_correlation_id
from apps.core.models import EventInbox
from apps.core.services import create_user_account

logger = logging.getLogger(__name__)


def _register_inbox(envelope: EventEnvelope, handler: str) -> bool:
    """Returns True si debe procesarse; False si duplicado."""
    if EventInbox.objects.filter(event_id=envelope.event_id).exists():
        logger.info("inbox_duplicate", extra={"event_id": envelope.event_id})
        return False
    EventInbox.objects.create(
        event_id=envelope.event_id,
        event_name=envelope.event_name,
        handler=handler,
    )
    return True


def handle_user_create_requested(envelope: EventEnvelope) -> None:
    handler = "user_create_requested"
    if not _register_inbox(envelope, handler):
        return

    set_correlation_id(envelope.correlation_id)
    payload = envelope.payload
    email = payload.get("email")
    nombre = payload.get("nombre")
    rol = payload.get("rol")
    password = payload.get("password") or payload.get("temporary_password")

    if not all([email, nombre, rol, password]):
        logger.error(
            "user.create_requested invalid payload",
            extra={"event_id": envelope.event_id},
        )
        return

    user, error = create_user_account(
        email=email,
        nombre=nombre,
        rol=rol,
        password=password,
        activo=payload.get("activo", True),
    )
    if error:
        logger.warning(
            "user.create_requested failed",
            extra={"event_id": envelope.event_id, "error": error},
        )
        return

    logger.info(
        "user.create_requested processed",
        extra={"event_id": envelope.event_id, "user_id": user.pk},
    )
