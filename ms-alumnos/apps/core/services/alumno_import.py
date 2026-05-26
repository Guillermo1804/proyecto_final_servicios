"""Logica de importacion masiva de alumnos (transaccional + outbox)."""

from __future__ import annotations

import logging

from django.conf import settings
from django.db import transaction

from apps.core.event_bus.publishers import publish_alumno_imported, publish_alumno_updated
from apps.core.models import Alumno, InscripcionMateria
from apps.core.services.alumno_ms1_sync import ensure_alumno_ms1_on_import
from apps.core.services.identity import password_from_email
from apps.core.services.materia_context import resolve_materia_context
from utils.notificaciones_client import send_bienvenida

logger = logging.getLogger(__name__)


def _use_event_bus() -> bool:
    return bool(getattr(settings, "USE_EVENT_BUS", False))


def _resolve_email(matricula: str, data: dict, existing: Alumno | None) -> str:
    email = (data.get("email") or "").strip().lower()
    if email:
        return email
    if existing and existing.email:
        return existing.email
    return f"{matricula}@alumno.buap.mx"


def _upsert_inscripcion(alumno: Alumno, materia_ctx: dict) -> bool:
    """Inscribe al alumno en la materia; retorna True si se creo inscripcion nueva."""
    materia_id = int(materia_ctx.get("materia_id") or 0)
    if materia_id <= 0:
        return False

    insc = InscripcionMateria.objects.filter(alumno=alumno, materia_id=materia_id).first()
    defaults = {
        "nrc": materia_ctx.get("nrc") or "",
        "nombre_materia": materia_ctx.get("materia_nombre") or "",
        "docente_nombre": materia_ctx.get("docente_nombre") or "",
        "horario": materia_ctx.get("horario") or "",
        "activa": True,
        "fecha_baja": None,
    }

    if insc:
        was_active = insc.activa
        for key, value in defaults.items():
            setattr(insc, key, value)
        insc.save()
        return not was_active

    InscripcionMateria.objects.create(alumno=alumno, materia_id=materia_id, **defaults)
    return True


def process_alumno_import_batch(
    alumnos_data: list,
    *,
    materia_id: int = 0,
    periodo_id: int = 0,
    docente_email: str = "",
) -> tuple[int, int, int]:
    """
    Upsert de alumnos + inscripcion opcional por materia_id.
    Retorna (creados, actualizados, inscritos).
    """
    creados = 0
    actualizados = 0
    inscritos = 0

    materia_ctx_base = resolve_materia_context(
        int(materia_id or 0),
        fallback_docente_email=docente_email,
        fallback_periodo_id=periodo_id,
    )

    with transaction.atomic():
        for data in alumnos_data:
            matricula = str(data.get("matricula") or "").strip()
            if not matricula:
                continue

            row_materia_id = int(data.get("materia_id") or materia_id or 0)
            row_periodo_id = int(data.get("periodo_id") or periodo_id or 0)
            row_docente_email = (data.get("docente_email") or docente_email or "").strip()

            materia_ctx = resolve_materia_context(
                row_materia_id,
                fallback_docente_email=row_docente_email,
                fallback_periodo_id=row_periodo_id,
            )
            if row_materia_id <= 0 and materia_ctx_base["materia_id"] > 0:
                materia_ctx = materia_ctx_base

            existing = Alumno.objects.filter(matricula=matricula).first()
            email = _resolve_email(matricula, data, existing)
            nombre_completo = f"{data.get('nombre', '')} {data.get('apellido', '')}".strip()

            usuario_id = int(data.get("usuario_id") or 0) or None
            if existing and existing.usuario_id:
                usuario_id = existing.usuario_id

            alumno, created = Alumno.objects.update_or_create(
                matricula=matricula,
                defaults={
                    "nombre": data.get("nombre") or (existing.nombre if existing else ""),
                    "apellido": data.get("apellido") or (existing.apellido if existing else ""),
                    "email": email,
                    "carrera": data.get("carrera") or (existing.carrera if existing else "ICC"),
                    "semestre": int(data.get("semestre") or (existing.semestre if existing else 1)),
                    "usuario_id": usuario_id,
                },
            )

            clave_acceso = (data.get("clave_acceso") or "").strip()
            nueva_inscripcion = _upsert_inscripcion(alumno, materia_ctx)
            if nueva_inscripcion:
                inscritos += 1

            if not alumno.usuario_id:
                clave_acceso = ensure_alumno_ms1_on_import(
                    alumno,
                    nombre_completo=nombre_completo,
                    password_hint=clave_acceso,
                    use_event_bus=_use_event_bus(),
                )
                alumno.refresh_from_db(fields=["usuario_id"])

            if created:
                creados += 1

                if _use_event_bus() and (clave_acceso or materia_ctx["materia_id"] > 0):
                    if clave_acceso or nueva_inscripcion:
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
                elif not _use_event_bus() and clave_acceso:
                    send_bienvenida(
                        alumno,
                        materia_id=row_materia_id,
                        clave_acceso=clave_acceso,
                    )
            else:
                actualizados += 1
                if not alumno.usuario_id:
                    logger.info(
                        "Import %s: alumno actualizado sin usuario MS-1 (reintentar Activar).",
                        matricula,
                    )
                if _use_event_bus():
                    if nueva_inscripcion and materia_ctx["materia_id"] > 0:
                        publish_alumno_imported(
                            alumno,
                            materia_id=materia_ctx["materia_id"],
                            periodo_id=materia_ctx["periodo_id"],
                            docente_email=materia_ctx["docente_email"],
                            clave_acceso=clave_acceso or password_from_email(alumno.email),
                            docente_nombre=materia_ctx["docente_nombre"],
                            materia_nombre=materia_ctx["materia_nombre"],
                            nrc=materia_ctx["nrc"],
                        )
                    else:
                        publish_alumno_updated(alumno)

    return creados, actualizados, inscritos
