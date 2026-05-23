"""Publicación de eventos de dominio MS-5 vía outbox."""

from __future__ import annotations

from django.db import transaction

from apps.core.event_bus.outbox import enqueue_domain_event


def publish_qr_session_created(
    *,
    sesion_id: int,
    materia_id: int,
    docente_id: int,
    fecha_fin_teorica: str,
) -> None:
    enqueue_domain_event(
        event_name='qr.session.created.v1',
        aggregate_type='qr_session',
        aggregate_id=str(sesion_id),
        payload={
            'sesion_id': sesion_id,
            'materia_id': materia_id,
            'docente_id': docente_id,
            'fecha_fin_teorica': fecha_fin_teorica,
        },
    )


def publish_asistencia_registered(
    *,
    sesion_id: int,
    materia_id: int,
    alumno_id: int,
    estado: str,
    minuto_registro: int,
    registro_id: int,
) -> None:
    enqueue_domain_event(
        event_name='asistencia.registered.v1',
        aggregate_type='asistencia',
        aggregate_id=str(registro_id),
        payload={
            'sesion_id': sesion_id,
            'materia_id': materia_id,
            'alumno_id': alumno_id,
            'estado': estado,
            'minuto_registro': minuto_registro,
            'registro_id': registro_id,
        },
    )


def publish_asistencia_rejected(
    *,
    materia_id: int,
    alumno_id: int,
    motivo: str,
    codigo: str,
    sesion_id: int | None = None,
) -> None:
    """Persiste rechazo en outbox en transacción propia (sobrevive al rollback del escaneo)."""
    with transaction.atomic():
        enqueue_domain_event(
            event_name='asistencia.rejected.v1',
            aggregate_type='asistencia',
            aggregate_id=f'{materia_id}-{alumno_id}',
            payload={
                'sesion_id': sesion_id,
                'materia_id': materia_id,
                'alumno_id': alumno_id,
                'motivo': motivo[:500],
                'codigo': codigo,
            },
            on_commit=False,
        )
