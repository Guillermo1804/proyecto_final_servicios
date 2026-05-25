"""Vincula docentes de MS-3 con usuarios de MS-1."""

from __future__ import annotations

from apps.core.models import Docente, PendingUserCreation
from apps.core.services.identity import password_from_email
from utils.auth_ms1_client import create_user_in_auth


def provision_docente_usuario(
    docente: Docente,
    authorization_header: str | None = None,
) -> tuple[Docente, str | None]:
    """
    Crea o reutiliza usuario en MS-1 y guarda docente.usuario_id.
    Retorna (docente_actualizado, error).
    """
    if docente.usuario_id:
        return docente, None

    nombre_completo = f"{docente.nombre} {docente.apellido}".strip()
    password = password_from_email(docente.email)

    user_id, err = create_user_in_auth(
        docente.email,
        nombre_completo,
        "docente",
        password,
        authorization_header=authorization_header,
    )
    if not user_id:
        return docente, err or "No se pudo crear el usuario en MS-1"

    docente.usuario_id = int(user_id)
    docente.save(update_fields=["usuario_id"])

    PendingUserCreation.objects.filter(
        entity_type=PendingUserCreation.EntityType.DOCENTE,
        entity_id=docente.pk,
        status=PendingUserCreation.Status.PENDING,
    ).update(
        status=PendingUserCreation.Status.COMPLETED,
        ms1_user_id=int(user_id),
        last_error=None,
    )

    return docente, None
