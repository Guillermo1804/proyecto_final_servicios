import logging
import os
import sys
import grpc
from decouple import config

# Dynamically add proto_generated to sys.path to avoid ModuleNotFoundError
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "proto_generated"))

from proto_generated import auth_pb2
from grpc_clients.auth_client import get_auth_stub

logger = logging.getLogger(__name__)

def _grpc_timeout() -> float:
    return float(config('GRPC_CLIENT_TIMEOUT', default=5))

def create_user_in_auth(email: str, nombre: str, rol: str, password: str) -> tuple[int | None, str | None]:
    """
    Calls MS-1 Auth CreateUser gRPC endpoint.
    Returns (user_id, None) on success or (None, error_message) on failure (graceful).
    """
    try:
        stub = get_auth_stub()
        request = auth_pb2.CreateUserRequest(
            email=email,
            nombre=nombre,
            rol=rol,
            password=password
        )
        response = stub.CreateUser(request, timeout=_grpc_timeout())
        if response.success and response.user_id:
            return response.user_id, None
        return None, response.message or "No se pudo crear el usuario en MS-1"
    except grpc.RpcError as exc:
        logger.warning("MS-1 CreateUser falló por gRPC: %s", exc.code())
        return None, exc.details() or str(exc)
    except Exception as exc:
        logger.error("Error inesperado CreateUser MS-1: %s", exc)
        return None, str(exc)
