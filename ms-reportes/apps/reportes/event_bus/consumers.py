"""Handlers idempotentes del worker consumidor MS-7."""

from __future__ import annotations

import logging

from agm_events.envelope import EventEnvelope
from agm_events.validation import validate_full_event

from apps.reportes.event_bus import projection_service as proj
from apps.reportes.event_bus.inbox import try_register_event
logger = logging.getLogger(__name__)


def _consume(envelope: EventEnvelope, handler: str, fn) -> None:
    logger.info(
        'event_received',
        extra={
            'event_id': str(envelope.event_id),
            'event_name': envelope.event_name,
            'handler': handler,
        },
    )
    validate_full_event(envelope)
    if not try_register_event(envelope, handler):
        return
    fn(envelope.payload)
    logger.info(
        'projection_updated',
        extra={'event_id': str(envelope.event_id), 'handler': handler},
    )


def handle_periodo_created(envelope: EventEnvelope) -> None:
    _consume(envelope, 'periodo_created', lambda p: proj.upsert_periodo(p))


def handle_periodo_updated(envelope: EventEnvelope) -> None:
    _consume(envelope, 'periodo_updated', lambda p: proj.upsert_periodo(p))


def handle_periodo_activated(envelope: EventEnvelope) -> None:
    _consume(envelope, 'periodo_activated', lambda p: proj.upsert_periodo(p, activo=True))


def handle_periodo_closed(envelope: EventEnvelope) -> None:
    _consume(envelope, 'periodo_closed', lambda p: proj.upsert_periodo(p, activo=False))


def handle_materia_created(envelope: EventEnvelope) -> None:
    _consume(envelope, 'materia_created', proj.upsert_materia)


def handle_materia_updated(envelope: EventEnvelope) -> None:
    _consume(envelope, 'materia_updated', proj.upsert_materia)


def handle_materia_assigned_teacher(envelope: EventEnvelope) -> None:
    _consume(envelope, 'materia_assigned_teacher', proj.upsert_materia)


def handle_materia_closed(envelope: EventEnvelope) -> None:
    _consume(envelope, 'materia_closed', proj.mark_materia_closed)


def handle_alumno_imported(envelope: EventEnvelope) -> None:
    _consume(envelope, 'alumno_imported', proj.handle_alumno_imported)


def handle_alumno_updated(envelope: EventEnvelope) -> None:
    _consume(envelope, 'alumno_updated', proj.handle_alumno_updated)


def handle_alumno_withdrawn(envelope: EventEnvelope) -> None:
    _consume(envelope, 'alumno_withdrawn', proj.handle_alumno_withdrawn)


def handle_actividad_created(envelope: EventEnvelope) -> None:
    _consume(envelope, 'actividad_created', proj.handle_actividad_created)


def handle_calificacion_updated(envelope: EventEnvelope) -> None:
    _consume(envelope, 'calificacion_updated', proj.handle_calificacion_updated)


def handle_concentrado_calculado(envelope: EventEnvelope) -> None:
    _consume(envelope, 'concentrado_calculado', proj.handle_concentrado_calculado)


def handle_calificaciones_cerradas(envelope: EventEnvelope) -> None:
    _consume(envelope, 'calificaciones_cerradas', proj.mark_calificaciones_cerradas)


def handle_asistencia_registered(envelope: EventEnvelope) -> None:
    _consume(envelope, 'asistencia_registered', proj.handle_asistencia_registered)


def handle_asistencia_rejected(envelope: EventEnvelope) -> None:
    _consume(envelope, 'asistencia_rejected', proj.handle_asistencia_rejected)


def handle_qr_session_created(envelope: EventEnvelope) -> None:
    _consume(envelope, 'qr_session_created', proj.handle_qr_session_created)


def handle_token_revoked(envelope: EventEnvelope) -> None:
    from agm_events.token_revoked import handle_token_revoked as _apply

    _apply(envelope)


HANDLERS = {
    'token.revoked.v1': handle_token_revoked,
    'periodo.created.v1': handle_periodo_created,
    'periodo.updated.v1': handle_periodo_updated,
    'periodo.activated.v1': handle_periodo_activated,
    'periodo.closed.v1': handle_periodo_closed,
    'materia.created.v1': handle_materia_created,
    'materia.updated.v1': handle_materia_updated,
    'materia.assigned_teacher.v1': handle_materia_assigned_teacher,
    'materia.closed.v1': handle_materia_closed,
    'alumno.imported.v1': handle_alumno_imported,
    'alumno.updated.v1': handle_alumno_updated,
    'alumno.withdrawn.v1': handle_alumno_withdrawn,
    'actividad.created.v1': handle_actividad_created,
    'calificacion.updated.v1': handle_calificacion_updated,
    'concentrado.calculado.v1': handle_concentrado_calculado,
    'materia.calificaciones_cerradas.v1': handle_calificaciones_cerradas,
    'asistencia.registered.v1': handle_asistencia_registered,
    'asistencia.rejected.v1': handle_asistencia_rejected,
    'qr.session.created.v1': handle_qr_session_created,
}
