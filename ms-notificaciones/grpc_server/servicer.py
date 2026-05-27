import logging
from typing import Any, Dict

import grpc

from apps.notificaciones.exceptions import (
    AlumnoNotFound,
    DocenteNotFound,
    MateriaNotFound,
    NotificacionesDomainError,
    UpstreamUnavailable,
)
from apps.notificaciones.services.email_service import EmailService
from proto_generated import notificaciones_pb2, notificaciones_pb2_grpc

logger = logging.getLogger(__name__)


def _grpc_code_for_message(message: str) -> grpc.StatusCode:
    lower = (message or '').lower()
    if 'no encontrado' in lower or 'no encontrada' in lower or 'not found' in lower:
        return grpc.StatusCode.NOT_FOUND
    if 'no disponible' in lower or 'timeout' in lower or 'unavailable' in lower:
        return grpc.StatusCode.UNAVAILABLE
    return grpc.StatusCode.INVALID_ARGUMENT


def _abort_domain(context, exc: NotificacionesDomainError) -> None:
    if isinstance(exc, (AlumnoNotFound, DocenteNotFound, MateriaNotFound)):
        context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
    if isinstance(exc, UpstreamUnavailable):
        context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))
    context.abort(grpc.StatusCode.INTERNAL, str(exc))


def _abort_from_result(context, result: Dict[str, Any]) -> None:
    message = result.get('message', 'Error al enviar correo')
    context.abort(_grpc_code_for_message(message), message)


def _send_response(result: Dict[str, Any]) -> notificaciones_pb2.SendResponse:
    return notificaciones_pb2.SendResponse(
        success=True,
        message=result.get('message', 'OK'),
    )


def _invoke_email(context, callback):
    """Ejecuta EmailService; propaga abort() y mapea excepciones de dominio."""
    try:
        return callback()
    except NotificacionesDomainError as exc:
        _abort_domain(context, exc)
    except Exception as exc:
        if exc.__class__.__name__ == 'AbortError':
            raise
        logger.exception('Error inesperado en RPC notificaciones')
        context.abort(grpc.StatusCode.INTERNAL, str(exc))


class NotificacionesServicer(notificaciones_pb2_grpc.NotificacionesServiceServicer):
    """Controlador gRPC: delega en EmailService sin duplicar lógica SMTP/historial."""

    def __init__(self, email_service: EmailService | None = None):
        self._email = email_service or EmailService()

    def SendBienvenida(self, request, context):
        if request.alumno_id <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, 'alumno_id debe ser mayor a 0')
        if not (request.clave_acceso or '').strip():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, 'clave_acceso es obligatoria')

        def _call():
            return self._email.send_bienvenida(
                request.alumno_id,
                request.materia_id,
                request.clave_acceso.strip(),
            )

        result = _invoke_email(context, _call)
        if not result.get('success'):
            _abort_from_result(context, result)
        return _send_response(result)

    def SendBajaNotif(self, request, context):
        if request.alumno_id <= 0 or request.docente_id <= 0 or request.materia_id <= 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                'alumno_id, docente_id y materia_id deben ser mayores a 0',
            )

        def _call():
            return self._email.send_baja(
                request.alumno_id,
                request.docente_id,
                request.materia_id,
            )

        result = _invoke_email(context, _call)
        if not result.get('success'):
            _abort_from_result(context, result)
        return _send_response(result)

    def SendCierreMateria(self, request, context):
        if request.materia_id <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, 'materia_id debe ser mayor a 0')

        def _call():
            return self._email.send_cierre_materia(request.materia_id)

        result = _invoke_email(context, _call)
        if not result.get('success'):
            if result.get('enviados', 0) == 0:
                _abort_from_result(context, result)
            return notificaciones_pb2.SendResponse(
                success=False,
                message=result.get('message', 'Envío masivo con fallos'),
            )
        return notificaciones_pb2.SendResponse(
            success=True,
            message=result.get('message', 'OK'),
        )

    def SendResetPassword(self, request, context):
        delivery = request.delivery
        email = (delivery.email if delivery else '').strip()
        reset_url = (delivery.reset_url if delivery else '').strip()
        nombre = (delivery.nombre if delivery else '').strip()
        if not email or not reset_url:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                'email y reset_url son obligatorios',
            )

        def _call():
            return self._email.send_reset_password(email, reset_url, nombre=nombre)

        result = _invoke_email(context, _call)
        if not result.get('success'):
            _abort_from_result(context, result)
        return _send_response(result)
