import logging
import sys
from pathlib import Path

import grpc
from decouple import config

logger = logging.getLogger(__name__)

PROTO_GENERATED_DIR = Path(__file__).resolve().parents[2] / 'proto_generated'
if str(PROTO_GENERATED_DIR) not in sys.path:
    sys.path.insert(0, str(PROTO_GENERATED_DIR))


def send_reset_password_notification(email, token, reset_url, timeout_seconds=5):
    """Envía la notificación de reseteo de contraseña vía gRPC a MS-6."""
    try:
        import notificaciones_pb2
        import notificaciones_pb2_grpc
    except ImportError:
        logger.warning('Dependencias grpc/protobuf no disponibles para MS-6')
        return False, 'Dependencias grpc/protobuf no disponibles'

    host = config('MS_NOTIFICACIONES_GRPC_HOST', default='ms-notificaciones')
    port = config('MS_NOTIFICACIONES_GRPC_PORT', default='50056')
    target = f'{host}:{port}'
    timeout = float(config('GRPC_CLIENT_TIMEOUT', default=timeout_seconds))

    try:
        with grpc.insecure_channel(target) as channel:
            stub = notificaciones_pb2_grpc.NotificacionesServiceStub(channel)
            response = stub.SendResetPassword(
                notificaciones_pb2.SendResetPasswordRequest(
                    email=email,
                    token=token,
                    reset_url=reset_url,
                ),
                timeout=timeout,
            )
            if not response.success:
                logger.warning(
                    'MS-6 SendResetPassword respondió success=false para %s: %s',
                    email,
                    response.message,
                )
            return bool(response.success), response.message
    except grpc.RpcError as exc:
        logger.warning(
            'MS-6 no disponible al enviar reset password (%s): %s',
            email,
            exc.code(),
        )
        return False, exc.details() or 'Error enviando notificación'
    except Exception as exc:
        logger.warning('Error inesperado al notificar reset a MS-6: %s', exc)
        return False, 'Error enviando notificación'
