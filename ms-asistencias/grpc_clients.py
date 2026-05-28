"""gRPC clients for MS-5 Asistencias QR.

Connects to:
- MS-1 (Auth): ValidateToken
- MS-3 (Alumnos): GetAlumnoById, IsAlumnoEnMateria
"""



"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""
from agm_events.grpc_legacy import block_business_grpc

import grpc
from decouple import config
from grpc import StatusCode

from proto_generated import (
    agm_common_pb2,
    alumnos_pb2,
    alumnos_pb2_grpc,
    auth_pb2,
    auth_pb2_grpc,
)

# ===== MS-1 Auth Configuration =====
AUTH_HOST = config('MS_AUTH_GRPC_HOST', default='ms-auth')
AUTH_PORT = config('MS_AUTH_GRPC_PORT', default='50051')

# ===== MS-3 Alumnos Configuration =====
ALUMNOS_HOST = config('MS_ALUMNOS_GRPC_HOST', default='ms-alumnos')
ALUMNOS_PORT = config('MS_ALUMNOS_GRPC_PORT', default='50053')

TIMEOUT = float(config('GRPC_CALL_TIMEOUT', default='5'))

_channel_auth = None
_channel_alumnos = None


def _get_channel(host, port):
    block_business_grpc('grpc_clients.py._get_channel')
    """Create an insecure gRPC channel."""
    return grpc.insecure_channel(f"{host}:{port}")


def auth_channel():
    block_business_grpc('grpc_clients.py.auth_channel')
    """Get or create MS-1 Auth channel."""
    global _channel_auth
    if _channel_auth is None:
        _channel_auth = _get_channel(AUTH_HOST, AUTH_PORT)
    return _channel_auth


def alumnos_channel():
    block_business_grpc('grpc_clients.py.alumnos_channel')
    """Get or create MS-3 Alumnos channel."""
    global _channel_alumnos
    if _channel_alumnos is None:
        _channel_alumnos = _get_channel(ALUMNOS_HOST, ALUMNOS_PORT)
    return _channel_alumnos


# ===== MS-1: Auth =====
def validate_token(token: str) -> dict:
    block_business_grpc('grpc_clients.py.validate_token')
    """Validate JWT token against MS-1 (Auth).
    
    Returns dict with user_id, role, etc. if valid.
    Raises grpc.RpcError if invalid.
    """
    stub = auth_pb2_grpc.AuthServiceStub(auth_channel())
    req = auth_pb2.ValidateTokenRequest(
        credential=agm_common_pb2.AccessTokenCredential(access_token=token),
    )
    try:
        response = stub.ValidateToken(req, timeout=TIMEOUT)
        user = response.result.user
        return {
            'user_id': user.user_id,
            'role': user.rol,
            'email': user.email,
        }
    except grpc.RpcError as e:
        raise


# ===== MS-3: Alumnos =====
def get_alumno_by_id(alumno_id: int):
    block_business_grpc('grpc_clients.py.get_alumno_by_id')
    """Get student info from MS-3 by ID."""
    stub = alumnos_pb2_grpc.AlumnosServiceStub(alumnos_channel())
    req = alumnos_pb2.GetAlumnoByIdRequest(alumno_id=alumno_id)
    try:
        return stub.GetAlumnoById(req, timeout=TIMEOUT)
    except grpc.RpcError as e:
        code = e.code()
        if code == StatusCode.NOT_FOUND:
            raise LookupError(e.details())
        raise


def is_alumno_en_materia(alumno_id: int, materia_id: int) -> bool:
    block_business_grpc('grpc_clients.py.is_alumno_en_materia')
    """Check if student is enrolled in a subject (MS-3).
    
    Returns True if enrolled, False otherwise.
    """
    stub = alumnos_pb2_grpc.AlumnosServiceStub(alumnos_channel())
    req = alumnos_pb2.IsAlumnoEnMateriaRequest(alumno_id=alumno_id, materia_id=materia_id)
    try:
        response = stub.IsAlumnoEnMateria(req, timeout=TIMEOUT)
        return response.enrolled
    except grpc.RpcError as e:
        code = e.code()
        if code == StatusCode.NOT_FOUND:
            return False
        raise
