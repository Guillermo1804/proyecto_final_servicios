from pathlib import Path
import sys
from decouple import config

PROTO_GENERATED_DIR = Path(__file__).resolve().parents[2] / 'proto_generated'
if str(PROTO_GENERATED_DIR) not in sys.path:
    sys.path.insert(0, str(PROTO_GENERATED_DIR))


def send_reset_password_notification(email, token, reset_url, timeout_seconds=5):
    """Envía la notificación de reseteo de contraseña vía gRPC a MS-6."""
    try:
        import grpc
        import notificaciones_pb2
        import notificaciones_pb2_grpc
    except ImportError:
        return False, 'Dependencias grpc/protobuf no disponibles'

    host = config('MS_NOTIFICACIONES_GRPC_HOST', default='ms-notificaciones')
    port = config('MS_NOTIFICACIONES_GRPC_PORT', default='50056')
    target = f'{host}:{port}'

    try:
        with grpc.insecure_channel(target) as channel:
            stub = notificaciones_pb2_grpc.NotificacionesServiceStub(channel)
            response = stub.SendResetPassword(
                notificaciones_pb2.SendResetPasswordRequest(
                    email=email,
                    token=token,
                    reset_url=reset_url,
                ),
                timeout=timeout_seconds,
            )
            return bool(response.success), response.message
    except grpc.RpcError as exc:
        return False, getattr(exc, 'details', lambda: 'Error enviando notificación')()
    except Exception:
        return False, 'Error enviando notificación'
