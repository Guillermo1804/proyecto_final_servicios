"""Publicacion de eventos de dominio MS-3."""

from __future__ import annotations

from apps.core.event_bus.outbox import enqueue_domain_event
from apps.core.event_bus.payloads import (
    alumno_imported_payload,
    alumno_updated_payload,
    alumno_withdrawn_payload,
    docente_imported_payload,
)
from apps.core.models import Alumno, Docente, InscripcionMateria


def publish_alumno_imported(
    alumno: Alumno,
    *,
    materia_id: int,
    periodo_id: int,
    docente_email: str,
    clave_acceso: str = "",
    docente_nombre: str = "",
    materia_nombre: str = "",
    nrc: str = "",
) -> None:
    enqueue_domain_event(
        event_name="alumno.imported.v1",
        aggregate_type="alumno",
        aggregate_id=str(alumno.pk),
        payload=alumno_imported_payload(
            alumno,
            materia_id=materia_id,
            periodo_id=periodo_id,
            docente_email=docente_email,
            clave_acceso=clave_acceso,
            docente_nombre=docente_nombre,
            materia_nombre=materia_nombre,
            nrc=nrc,
        ),
    )


def publish_alumno_updated(alumno: Alumno) -> None:
    enqueue_domain_event(
        event_name="alumno.updated.v1",
        aggregate_type="alumno",
        aggregate_id=str(alumno.pk),
        payload=alumno_updated_payload(alumno),
    )


def publish_alumno_withdrawn(
    inscripcion: InscripcionMateria,
    *,
    periodo_id: int,
    docente_email: str,
    docente_id: int = 0,
) -> None:
    enqueue_domain_event(
        event_name="alumno.withdrawn.v1",
        aggregate_type="alumno",
        aggregate_id=str(inscripcion.alumno_id),
        payload=alumno_withdrawn_payload(
            inscripcion,
            periodo_id=periodo_id,
            docente_email=docente_email,
            docente_id=docente_id,
        ),
    )


def publish_docente_imported(docente: Docente, *, temporary_password: str) -> None:
    enqueue_domain_event(
        event_name="docente.imported.v1",
        aggregate_type="docente",
        aggregate_id=str(docente.pk),
        payload=docente_imported_payload(docente, temporary_password=temporary_password),
    )
