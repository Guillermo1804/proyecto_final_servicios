import logging
import uuid

import grpc
from decouple import config
from proto_generated import auth_pb2, auth_pb2_grpc

logger = logging.getLogger(__name__)


def _auth_target() -> str:
    host = config('MS_AUTH_GRPC_HOST', default='ms-auth')
    port = config('MS_AUTH_GRPC_PORT', default='50051')
    return f'{host}:{port}'


def _grpc_timeout() -> float:
    return float(config('GRPC_CLIENT_TIMEOUT', default=5))


def create_user_alumno(email: str, nombre: str) -> tuple[int | None, str | None, str | None]:
    """
    Crea usuario alumno en MS-1.
    Retorna (user_id, clave_acceso temporal, mensaje_error).
    """
    clave_acceso = str(uuid.uuid4())
    try:
        with grpc.insecure_channel(_auth_target()) as channel:
            stub = auth_pb2_grpc.AuthServiceStub(channel)
            response = stub.CreateUser(
                auth_pb2.CreateUserRequest(
                    email=email,
                    nombre=nombre,
                    rol='alumno',
                    password=clave_acceso,
                ),
                timeout=_grpc_timeout(),
            )
            if response.success and response.user_id:
                return response.user_id, clave_acceso, None
            return None, None, response.message or 'No se pudo crear el usuario en MS-1'
    except grpc.RpcError as exc:
        logger.warning('MS-1 CreateUser falló para %s: %s', email, exc.code())
        return None, None, exc.details() or str(exc)
    except Exception as exc:
        logger.error('Error inesperado CreateUser MS-1: %s', exc)
        return None, None, str(exc)
