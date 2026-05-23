"""Aprovisionamiento asincrono de usuarios en MS-1 via bus."""

from __future__ import annotations

import logging
import uuid

from django.conf import settings

from apps.core.event_bus.outbox import enqueue_domain_event
from apps.core.models import Alumno, Docente, PendingUserCreation

logger = logging.getLogger(__name__)


def _use_event_bus() -> bool:
    return bool(getattr(settings, "USE_EVENT_BUS", False))


def generate_temporary_password() -> str:
    return str(uuid.uuid4())[:12]


def request_user_creation(
    *,
    entity_type: str,
    entity: Alumno | Docente,
    email: str,
    nombre: str,
    rol: str,
    password: str | None = None,
) -> PendingUserCreation | None:
    """
    Registra solicitud local y publica user.create_requested.v1.
    Retorna PendingUserCreation si el bus esta activo; None si modo legacy.
    """
    if entity.usuario_id:
        return None

    temp_password = (password or "").strip() or generate_temporary_password()

    if not _use_event_bus():
        return None

    pending = PendingUserCreation.objects.create(
        entity_type=entity_type,
        entity_id=entity.pk,
        email=email,
        nombre=nombre,
        rol=rol,
        temporary_password=temp_password,
        status=PendingUserCreation.Status.PENDING,
    )

    enqueue_domain_event(
        event_name="user.create_requested.v1",
        aggregate_type="user",
        aggregate_id=str(pending.pk),
        payload={
            "email": email,
            "nombre": nombre,
            "rol": rol,
            "password": temp_password,
            "temporary_password": temp_password,
            "activo": True,
        },
        causation_id=str(pending.pk),
    )
    logger.info(
        "user_create_requested",
        extra={
            "pending_id": str(pending.pk),
            "entity_type": entity_type,
            "entity_id": entity.pk,
            "email": email,
        },
    )
    return pending
