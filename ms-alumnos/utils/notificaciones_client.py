import logging

import grpc
from decouple import config
from proto_generated import notificaciones_pb2, notificaciones_pb2_grpc

"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""
from agm_events.grpc_legacy import block_business_grpc

logger = logging.getLogger(__name__)


def _notificaciones_target() -> str:
    block_business_grpc('notificaciones_client.py._notificaciones_target')
    host = config('MS_NOTIFICACIONES_GRPC_HOST', default='ms-notificaciones')
    port = config('MS_NOTIFICACIONES_GRPC_PORT', default='50056')
    return f'{host}:{port}'


def _grpc_timeout() -> float:
    block_business_grpc('notificaciones_client.py._grpc_timeout')
    return float(config('GRPC_CLIENT_TIMEOUT', default=5))


def send_bienvenida(alumno, *, materia_id: int = 0, clave_acceso: str = '') -> bool:
    block_business_grpc('notificaciones_client.py.send_bienvenida')
    """Envía notificación de bienvenida al alumno vía gRPC a MS-6."""
    if not (clave_acceso or '').strip():
        logger.warning(
            'Omitiendo bienvenida para %s: clave_acceso vacía',
            getattr(alumno, 'matricula', alumno),
        )
        return False
    try:
        with grpc.insecure_channel(_notificaciones_target()) as channel:
            stub = notificaciones_pb2_grpc.NotificacionesServiceStub(channel)
            request = notificaciones_pb2.SendBienvenidaRequest(
                alumno_id=alumno.id,
                materia_id=int(materia_id or 0),
                clave_acceso=clave_acceso.strip(),
            )
            response = stub.SendBienvenida(request, timeout=_grpc_timeout())
            return response.success
    except grpc.RpcError as exc:
        logger.warning(
            'MS-6 no disponible o error RPC al notificar bienvenida %s: %s',
            getattr(alumno, 'matricula', alumno.id),
            exc.code(),
        )
        return False
    except Exception as exc:
        logger.error('Error inesperado al llamar a MS-6 (bienvenida): %s', exc)
        return False


def send_baja_notif(inscripcion, *, docente_id: int) -> bool:
    block_business_grpc('notificaciones_client.py.send_baja_notif')
    """Notifica al docente que un alumno se dio de baja vía gRPC a MS-6."""
    if docente_id <= 0:
        logger.warning(
            'Omitiendo baja-notif materia %s: docente_id inválido',
            inscripcion.materia_id,
        )
        return False
    try:
        with grpc.insecure_channel(_notificaciones_target()) as channel:
            stub = notificaciones_pb2_grpc.NotificacionesServiceStub(channel)
            request = notificaciones_pb2.SendBajaRequest(
                alumno_id=inscripcion.alumno.id,
                docente_id=int(docente_id),
                materia_id=inscripcion.materia_id,
            )
            response = stub.SendBajaNotif(request, timeout=_grpc_timeout())
            return response.success
    except grpc.RpcError as exc:
        logger.warning(
            'MS-6 no disponible o error RPC al notificar baja %s materia %s: %s',
            inscripcion.alumno.matricula,
            inscripcion.materia_id,
            exc.code(),
        )
        return False
    except Exception as exc:
        logger.error('Error inesperado al llamar a MS-6 (baja): %s', exc)
        return False
