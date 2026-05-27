"""Publicación de eventos de dominio MS-4 vía outbox."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from apps.core.event_bus.outbox import enqueue_domain_event


def publish_actividad_created(
    *,
    actividad_id: int,
    materia_id: int,
    ponderacion_id: int,
    nombre: str,
    descripcion: str = '',
    fecha: str | None = None,
    categoria: str = '',
) -> None:
    enqueue_domain_event(
        event_name='actividad.created.v1',
        aggregate_type='actividad',
        aggregate_id=str(actividad_id),
        payload={
            'actividad_id': actividad_id,
            'materia_id': materia_id,
            'ponderacion_id': ponderacion_id,
            'nombre': nombre,
            'descripcion': descripcion,
            'fecha': fecha,
            'categoria': categoria,
        },
    )


def publish_calificacion_updated(
    *,
    calificacion_id: int,
    actividad_id: int,
    alumno_id: int,
    materia_id: int,
    calificacion: Decimal,
    created: bool,
) -> None:
    enqueue_domain_event(
        event_name='calificacion.updated.v1',
        aggregate_type='calificacion',
        aggregate_id=str(calificacion_id),
        payload={
            'calificacion_id': calificacion_id,
            'actividad_id': actividad_id,
            'alumno_id': alumno_id,
            'materia_id': materia_id,
            'calificacion': float(calificacion),
            'created': created,
        },
    )


def publish_concentrado_calculado(
    *,
    materia_id: int,
    total_alumnos: int,
    promedio_grupal: float,
    nrc: str,
    materia_nombre: str,
) -> None:
    enqueue_domain_event(
        event_name='concentrado.calculado.v1',
        aggregate_type='concentrado',
        aggregate_id=str(materia_id),
        payload={
            'materia_id': materia_id,
            'total_alumnos': total_alumnos,
            'promedio_grupal': promedio_grupal,
            'nrc': nrc,
            'materia_nombre': materia_nombre,
        },
    )


def publish_materia_calificaciones_cerradas(payload: dict[str, Any]) -> None:
    enqueue_domain_event(
        event_name='materia.calificaciones_cerradas.v1',
        aggregate_type='materia',
        aggregate_id=str(payload['materia_id']),
        payload=payload,
    )
