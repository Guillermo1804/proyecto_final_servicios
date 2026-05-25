"""Vincula alumnos de MS-3 con usuarios de MS-1."""

from __future__ import annotations

from apps.core.models import Alumno, PendingUserCreation
from apps.core.services.identity import password_from_email
from utils.auth_ms1_client import create_user_in_auth, deactivate_user_in_auth


def provision_alumno_usuario(alumno: Alumno) -> tuple[Alumno, str | None]:
    """
    Crea o reutiliza usuario en MS-1 y guarda alumno.usuario_id.
    Retorna (alumno_actualizado, error).
    """
    if alumno.usuario_id:
        return alumno, None

    email = (alumno.email or "").strip().lower()
    if not email:
        return alumno, "El alumno no tiene correo registrado."

    nombre_completo = f"{alumno.nombre} {alumno.apellido}".strip() or alumno.matricula
    password = password_from_email(email)

    user_id, err = create_user_in_auth(
        email,
        nombre_completo,
        "alumno",
        password,
    )
    if not user_id:
        return alumno, err or "No se pudo crear el usuario en MS-1"

    alumno.usuario_id = int(user_id)
    alumno.save(update_fields=["usuario_id"])

    PendingUserCreation.objects.filter(
        entity_type=PendingUserCreation.EntityType.ALUMNO,
        entity_id=alumno.pk,
        status=PendingUserCreation.Status.PENDING,
    ).update(
        status=PendingUserCreation.Status.COMPLETED,
        ms1_user_id=int(user_id),
        last_error=None,
    )

    return alumno, None


def deprovision_alumno_usuario(alumno: Alumno) -> tuple[Alumno, str | None]:
    """
    Desactiva usuario en MS-1 (si existe) y limpia alumno.usuario_id en MS-3.
    """
    if not alumno.usuario_id:
        return alumno, None

    user_id = int(alumno.usuario_id)
    ms1_err = deactivate_user_in_auth(user_id)
    if ms1_err:
        return alumno, ms1_err

    alumno.usuario_id = None
    alumno.save(update_fields=["usuario_id"])

    PendingUserCreation.objects.filter(
        entity_type=PendingUserCreation.EntityType.ALUMNO,
        entity_id=alumno.pk,
        status=PendingUserCreation.Status.PENDING,
    ).update(
        status=PendingUserCreation.Status.FAILED,
        last_error="Desactivado manualmente desde MS-3",
    )

    return alumno, None
