"""Handlers de eventos consumidos por MS-6."""

from __future__ import annotations

import logging
import uuid

from agm_events.envelope import EventEnvelope
from agm_events.exceptions import EventValidationError
from agm_events.validation import validate_full_event

from apps.notificaciones.event_bus.inbox import try_register_event
from apps.notificaciones.event_bus.mail_worker import enqueue_mail_task
from apps.notificaciones.models import EstadoEnvioCorreo, HistorialCorreo, TipoCorreo
from apps.notificaciones.services.email_payload_service import EmailPayloadService
from apps.notificaciones.services.historial_service import HistorialService

logger = logging.getLogger(__name__)
_email = EmailPayloadService()


def _event_uuid(envelope: EventEnvelope) -> uuid.UUID:
    return uuid.UUID(str(envelope.event_id))


def _dispatch_after_inbox(envelope: EventEnvelope, handler: str, fn) -> None:
    eid = str(envelope.event_id)
    enqueue_mail_task(
        fn,
        event_id=eid,
        event_name=envelope.event_name,
    )


def handle_alumno_imported(envelope: EventEnvelope) -> None:
    handler = 'alumno_imported'
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
    logger.info(
        'schema_validated',
        extra={'event_id': str(envelope.event_id), 'event_name': envelope.event_name},
    )
    payload = envelope.payload
    eid = _event_uuid(envelope)

    def _send() -> None:
        try:
            _email.send_bienvenida_from_payload(payload, event_id=eid)
        except Exception as exc:
            _mark_dead_letter(eid, str(exc))

    _dispatch_after_inbox(envelope, handler, _send)


def handle_alumno_withdrawn(envelope: EventEnvelope) -> None:
    handler = 'alumno_withdrawn'
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
    logger.info('schema_validated', extra={'event_id': str(envelope.event_id)})
    payload = envelope.payload
    eid = _event_uuid(envelope)

    def _send() -> None:
        try:
            _email.send_baja_from_payload(payload, event_id=eid)
        except Exception as exc:
            _mark_dead_letter(eid, str(exc))

    _dispatch_after_inbox(envelope, handler, _send)


def handle_materia_closed(envelope: EventEnvelope) -> None:
    handler = 'materia_closed'
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
    payload = envelope.payload
    eid = _event_uuid(envelope)

    def _send() -> None:
        try:
            _email.send_cierre_from_payload(payload, event_id=eid)
        except Exception as exc:
            _mark_dead_letter(eid, str(exc))

    _dispatch_after_inbox(envelope, handler, _send)


def handle_password_reset_requested(envelope: EventEnvelope) -> None:
    handler = 'password_reset_requested'
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
    payload = envelope.payload
    eid = _event_uuid(envelope)

    def _send() -> None:
        try:
            _email.send_reset_from_payload(payload, event_id=eid)
        except Exception as exc:
            _mark_dead_letter(eid, str(exc))

    _dispatch_after_inbox(envelope, handler, _send)


def handle_invalid_schema(envelope: EventEnvelope, exc: EventValidationError) -> None:
    """Registra en historial/DLQ logico sin reintentar parseo."""
    logger.error(
        'schema_validation_failed',
        extra={
            'event_id': str(envelope.event_id),
            'event_name': envelope.event_name,
            'error': str(exc),
        },
    )
    try_register_event(envelope, 'schema_invalid')
    HistorialService.registrar(
        tipo=TipoCorreo.RESET_PASSWORD,
        destinatario_email='invalid@agm.local',
        asunto=f'Evento inválido: {envelope.event_name}',
        cuerpo=str(exc)[:2000],
        exitoso=False,
        error_msg=str(exc),
        event_id=envelope.event_id,
        estado_envio=EstadoEnvioCorreo.DEAD_LETTER,
    )


def _mark_dead_letter(event_id: uuid.UUID, error: str) -> None:
    HistorialCorreo.objects.filter(event_id=event_id).update(
        estado_envio=EstadoEnvioCorreo.DEAD_LETTER,
        error_msg=error[:2000],
        exitoso=False,
    )


def handle_materia_calificaciones_cerradas(envelope: EventEnvelope) -> None:
    """Cierre de actas desde MS-4 — mismo flujo de correo que materia.closed."""
    handle_materia_closed(envelope)


HANDLERS = {
    'alumno.imported.v1': handle_alumno_imported,
    'alumno.withdrawn.v1': handle_alumno_withdrawn,
    'materia.closed.v1': handle_materia_closed,
    'materia.calificaciones_cerradas.v1': handle_materia_calificaciones_cerradas,
    'password.reset_requested.v1': handle_password_reset_requested,
}
