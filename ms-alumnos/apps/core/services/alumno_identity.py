"""Resolucion del registro Alumno para el usuario autenticado (JWT)."""

from __future__ import annotations

import logging
import re

from apps.core.models import Alumno

logger = logging.getLogger(__name__)

_MATRICULA_RE = re.compile(r"^20\d{7,8}$")


def _matricula_from_email(email: str) -> str | None:
    local = (email or "").split("@", 1)[0].strip()
    if _MATRICULA_RE.match(local):
        return local
    return None


def resolve_alumno_for_request(request, *, link_usuario: bool = True) -> Alumno | None:
    """
    Busca el alumno del JWT:
    1) usuario_id
    2) email (y vincula usuario_id si estaba vacio)
    3) matricula derivada del email (2022XXXXX@alumno.buap.mx)
    """
    user_id = int(getattr(request, "user_id", 0) or 0)
    email = (getattr(request, "user_email", None) or "").strip().lower()

    alumno: Alumno | None = None

    if user_id > 0:
        alumno = Alumno.objects.filter(usuario_id=user_id).first()

    if not alumno and email:
        alumno = Alumno.objects.filter(email__iexact=email).first()

    if not alumno and email:
        matricula = _matricula_from_email(email)
        if matricula:
            alumno = Alumno.objects.filter(matricula=matricula).first()

    if not alumno:
        return None

    if link_usuario and user_id > 0 and not alumno.usuario_id:
        alumno.usuario_id = user_id
        if email and not (alumno.email or "").strip():
            alumno.email = email
        alumno.save(update_fields=["usuario_id", "email"])
        logger.info(
            "Alumno %s vinculado a usuario_id=%s por email/matricula",
            alumno.matricula,
            user_id,
        )

    return alumno
