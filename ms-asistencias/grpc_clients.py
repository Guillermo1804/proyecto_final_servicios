"""gRPC clients for MS-5 Asistencias QR.

Connects to:
- MS-1 (Auth): ValidateToken
- MS-3 (Alumnos): GetAlumnoById, IsAlumnoEnMateria
"""

import grpc
from decouple import config
from grpc import StatusCode

from proto_generated import alumnos_pb2_grpc, alumnos_pb2, auth_pb2_grpc, auth_pb2

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
    """Create an insecure gRPC channel."""
    return grpc.insecure_channel(f"{host}:{port}")


def auth_channel():
    """Get or create MS-1 Auth channel."""
    global _channel_auth
    if _channel_auth is None:
        _channel_auth = _get_channel(AUTH_HOST, AUTH_PORT)
    return _channel_auth


def alumnos_channel():
    """Get or create MS-3 Alumnos channel."""
    global _channel_alumnos
    if _channel_alumnos is None:
        _channel_alumnos = _get_channel(ALUMNOS_HOST, ALUMNOS_PORT)
    return _channel_alumnos


# ===== MS-1: Auth =====
def validate_token(token: str) -> dict:
    """Validate JWT token against MS-1 (Auth).
    
    Returns dict with user_id, role, etc. if valid.
    Raises grpc.RpcError if invalid.
    """
    stub = auth_pb2_grpc.AuthServiceStub(auth_channel())
    req = auth_pb2.ValidateTokenRequest(token=token)
    try:
        response = stub.ValidateToken(req, timeout=TIMEOUT)
        return {
            'user_id': response.user_id,
            'role': response.role,
            'email': response.email,
        }
    except grpc.RpcError as e:
        raise


# ===== MS-3: Alumnos =====
def get_alumno_by_id(alumno_id: int):
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
