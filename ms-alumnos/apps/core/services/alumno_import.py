"""Logica de importacion masiva de alumnos (transaccional + outbox)."""

from __future__ import annotations

import logging
import uuid

from django.conf import settings
from django.db import transaction

from apps.core.event_bus.publishers import publish_alumno_imported, publish_alumno_updated
from apps.core.models import Alumno, PendingUserCreation
from apps.core.services.identity import password_from_email, request_user_creation
from apps.core.services.materia_context import resolve_materia_context
from utils.auth_client import create_user_alumno
from utils.notificaciones_client import send_bienvenida

logger = logging.getLogger(__name__)


def _use_event_bus() -> bool:
    return bool(getattr(settings, "USE_EVENT_BUS", False))


def process_alumno_import_batch(alumnos_data: list) -> tuple[int, int]:
    """Upsert de alumnos en una sola transaccion; eventos en on_commit."""
    creados = 0
    actualizados = 0

    with transaction.atomic():
        for data in alumnos_data:
            matricula = data.get("matricula")
            if not matricula:
                continue

            usuario_id = int(data.get("usuario_id") or 0) or None
            clave_acceso = (data.get("clave_acceso") or "").strip()
            materia_id = int(data.get("materia_id") or 0)
            periodo_id = int(data.get("periodo_id") or 0)
            docente_email = (data.get("docente_email") or "").strip()
            nombre_completo = f"{data.get('nombre', '')} {data.get('apellido', '')}".strip()

            materia_ctx = resolve_materia_context(
                materia_id,
                fallback_docente_email=docente_email,
                fallback_periodo_id=periodo_id,
            )

            alumno, created = Alumno.objects.update_or_create(
                matricula=matricula,
                defaults={
                    "nombre": data.get("nombre"),
                    "apellido": data.get("apellido"),
                    "email": data.get("email"),
                    "carrera": data.get("carrera", "ICC"),
                    "semestre": data.get("semestre", 1),
                    "usuario_id": usuario_id,
                },
            )

            if created:
                creados += 1
                password = clave_acceso or password_from_email(alumno.email)

                if not alumno.usuario_id:
                    if _use_event_bus():
                        request_user_creation(
                            entity_type=PendingUserCreation.EntityType.ALUMNO,
                            entity=alumno,
                            email=alumno.email,
                            nombre=nombre_completo or alumno.matricula,
                            rol="alumno",
                            password=password,
                        )
                        clave_acceso = password
                    else:
                        uid, clave_ms1, err = create_user_alumno(
                            alumno.email,
                            nombre_completo or alumno.matricula,
                        )
                        if uid:
                            alumno.usuario_id = uid
                            alumno.save(update_fields=["usuario_id"])
                            clave_acceso = clave_acceso or (clave_ms1 or "")
                        elif err:
                            logger.warning(
                                "Import %s: usuario MS-1 no creado (%s)",
                                matricula,
                                err,
                            )

                if _use_event_bus():
                    if clave_acceso:
                        publish_alumno_imported(
                            alumno,
                            materia_id=materia_ctx["materia_id"],
                            periodo_id=materia_ctx["periodo_id"],
                            docente_email=materia_ctx["docente_email"],
                            clave_acceso=clave_acceso,
                            docente_nombre=materia_ctx["docente_nombre"],
                            materia_nombre=materia_ctx["materia_nombre"],
                            nrc=materia_ctx["nrc"],
                        )
                else:
                    send_bienvenida(
                        alumno,
                        materia_id=materia_id,
                        clave_acceso=clave_acceso,
                    )
            else:
                actualizados += 1
                if _use_event_bus():
                    publish_alumno_updated(alumno)

    return creados, actualizados
