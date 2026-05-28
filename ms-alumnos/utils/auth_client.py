import logging
import os
import sys

import grpc
from decouple import config

# Dynamically add proto_generated to sys.path to avoid ModuleNotFoundError
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "proto_generated"))

from proto_generated import auth_pb2, auth_pb2_grpc

from apps.core.services.identity import password_from_email

"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""
from agm_events.grpc_legacy import block_business_grpc

logger = logging.getLogger(__name__)


def _auth_target() -> str:
    block_business_grpc('auth_client.py._auth_target')
    host = config('MS_AUTH_GRPC_HOST', default='ms-auth')
    port = config('MS_AUTH_GRPC_PORT', default='50051')
    return f'{host}:{port}'


def _grpc_timeout() -> float:
    block_business_grpc('auth_client.py._grpc_timeout')
    return float(config('GRPC_CLIENT_TIMEOUT', default=5))


def create_user_alumno(email: str, nombre: str) -> tuple[int | None, str | None, str | None]:
    block_business_grpc('auth_client.py.create_user_alumno')
    """
    Crea usuario alumno en MS-1.
    Retorna (user_id, clave_acceso temporal, mensaje_error).
    """
    clave_acceso = password_from_email(email)
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
