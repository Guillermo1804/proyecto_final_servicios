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


def send_cierre_materia(materia_id: int) -> bool:
    block_business_grpc('notificaciones_client.py.send_cierre_materia')
    """Notifica cierre de materia a todos los alumnos vía MS-6 (no aborta el cierre local)."""
    if materia_id <= 0:
        return False
    try:
        with grpc.insecure_channel(_notificaciones_target()) as channel:
            stub = notificaciones_pb2_grpc.NotificacionesServiceStub(channel)
            response = stub.SendCierreMateria(
                notificaciones_pb2.SendCierreMateriaRequest(materia_id=int(materia_id)),
                timeout=_grpc_timeout(),
            )
            if not response.success:
                logger.warning(
                    'MS-6 SendCierreMateria materia %s: %s',
                    materia_id,
                    response.message,
                )
            return response.success
    except grpc.RpcError as exc:
        logger.warning(
            'MS-6 no disponible al notificar cierre materia %s: %s',
            materia_id,
            exc.code(),
        )
        return False
    except Exception as exc:
        logger.error('Error inesperado SendCierreMateria materia %s: %s', materia_id, exc)
        return False
