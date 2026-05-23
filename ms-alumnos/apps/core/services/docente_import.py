"""Importacion de docentes desde PDF (transaccional + outbox)."""

from __future__ import annotations

import logging
from django.conf import settings
from django.db import transaction

from apps.core.event_bus.publishers import publish_docente_imported
from apps.core.models import Docente, PendingUserCreation
from apps.core.services.identity import generate_temporary_password, request_user_creation
from utils.auth_ms1_client import create_user_in_auth

logger = logging.getLogger(__name__)


def _use_event_bus() -> bool:
    return bool(getattr(settings, "USE_EVENT_BUS", False))


def process_docente_import_rows(rows: list[dict]) -> tuple[int, int, list]:
    """Crea docentes en lote; retorna (creados, omitidos, errores)."""
    creados = 0
    omitidos = 0
    errores: list = []

    with transaction.atomic():
        for row in rows:
            nombre = row["nombre"]
            apellido = row["apellido"]
            email = row["email"]
            departamento = row["departamento"]

            if Docente.objects.filter(email=email).exists():
                omitidos += 1
                continue

            temp_pwd = generate_temporary_password()
            usuario_id = None

            if _use_event_bus():
                try:
                    docente = Docente.objects.create(
                        usuario_id=None,
                        nombre=nombre,
                        apellido=apellido,
                        email=email,
                        departamento=departamento,
                    )
                    request_user_creation(
                        entity_type=PendingUserCreation.EntityType.DOCENTE,
                        entity=docente,
                        email=email,
                        nombre=f"{nombre} {apellido}".strip(),
                        rol="docente",
                        password=temp_pwd,
                    )
                    publish_docente_imported(docente, temporary_password=temp_pwd)
                    creados += 1
                except Exception as exc:
                    errores.append({"email": email, "error": f"Error de BD local: {exc}"})
            else:
                user_id, err_msg = create_user_in_auth(
                    email,
                    f"{nombre} {apellido}".strip(),
                    "docente",
                    temp_pwd,
                )
                if not user_id:
                    errores.append(
                        {"email": email, "error": err_msg or "Error en gRPC de MS-1 Auth"}
                    )
                    continue
                try:
                    Docente.objects.create(
                        usuario_id=user_id,
                        nombre=nombre,
                        apellido=apellido,
                        email=email,
                        departamento=departamento,
                    )
                    creados += 1
                except Exception as exc:
                    errores.append({"email": email, "error": f"Error de BD local: {exc}"})

    return creados, omitidos, errores
