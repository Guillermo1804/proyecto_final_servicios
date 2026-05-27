"""Sincronizacion de alumnos con MS-1 durante importacion."""

from __future__ import annotations

import logging

from apps.core.models import Alumno, PendingUserCreation
from apps.core.services.alumno_provision import provision_alumno_usuario
from apps.core.services.identity import password_from_email, request_user_creation

logger = logging.getLogger(__name__)


def ensure_alumno_ms1_on_import(
    alumno: Alumno,
    *,
    nombre_completo: str,
    password_hint: str = "",
    use_event_bus: bool,
) -> str:
    """
    Intenta activar alumno en MS-1 de forma sincrona al importar.
    Si falla y el bus esta activo, encola creacion asincrona.
    Retorna clave de acceso para notificaciones (aunque MS-1 falle).
    """
    if alumno.usuario_id:
        return password_hint or password_from_email(alumno.email)

    password = (password_hint or "").strip() or password_from_email(alumno.email)
    alumno, err = provision_alumno_usuario(alumno)
    if alumno.usuario_id:
        return password

    if use_event_bus:
        request_user_creation(
            entity_type=PendingUserCreation.EntityType.ALUMNO,
            entity=alumno,
            email=alumno.email,
            nombre=nombre_completo or alumno.matricula,
            rol="alumno",
            password=password,
        )
        if err:
            logger.warning(
                "Import %s: MS-1 no disponible (%s); encolado en bus.",
                alumno.matricula,
                err,
            )
    elif err:
        logger.warning(
            "Import %s: usuario MS-1 no creado (%s)",
            alumno.matricula,
            err,
        )

    return password
