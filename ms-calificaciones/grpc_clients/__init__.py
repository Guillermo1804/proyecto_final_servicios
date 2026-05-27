import grpc
from decouple import config
from grpc import StatusCode

from proto_generated import (
    agm_common_pb2,
    alumnos_pb2,
    alumnos_pb2_grpc,
    auth_pb2,
    auth_pb2_grpc,
    periodos_pb2,
    periodos_pb2_grpc,
)

"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""
from agm_events.grpc_legacy import block_business_grpc

ALUMNOS_HOST = config('MS_ALUMNOS_GRPC_HOST', default='ms-alumnos')
ALUMNOS_PORT = config('MS_ALUMNOS_GRPC_PORT', default='50053')
AUTH_HOST = config('MS_AUTH_GRPC_HOST', default='ms-auth')
AUTH_PORT = config('MS_AUTH_GRPC_PORT', default='50051')
PERIODOS_HOST = config('MS_PERIODOS_GRPC_HOST', default='ms-periodos')
PERIODOS_PORT = config('MS_PERIODOS_GRPC_PORT', default='50052')
TIMEOUT = float(config('GRPC_CALL_TIMEOUT', default='5'))

_channel_alumnos = None
_channel_auth = None
_channel_periodos = None


def _get_channel(host, port):
    block_business_grpc('__init__.py._get_channel')
    return grpc.insecure_channel(f"{host}:{port}")


def alumnos_channel():
    block_business_grpc('__init__.py.alumnos_channel')
    global _channel_alumnos
    if _channel_alumnos is None:
        _channel_alumnos = _get_channel(ALUMNOS_HOST, ALUMNOS_PORT)
    return _channel_alumnos


def auth_channel():
    block_business_grpc('__init__.py.auth_channel')
    global _channel_auth
    if _channel_auth is None:
        _channel_auth = _get_channel(AUTH_HOST, AUTH_PORT)
    return _channel_auth


def periodos_channel():
    block_business_grpc('__init__.py.periodos_channel')
    global _channel_periodos
    if _channel_periodos is None:
        _channel_periodos = _get_channel(PERIODOS_HOST, PERIODOS_PORT)
    return _channel_periodos


def get_alumno_by_id(alumno_id):
    block_business_grpc('__init__.py.get_alumno_by_id')
    stub = alumnos_pb2_grpc.AlumnosServiceStub(alumnos_channel())
    req = alumnos_pb2.GetAlumnoByIdRequest(alumno_id=alumno_id)
    try:
        return stub.GetAlumnoById(req, timeout=TIMEOUT)
    except grpc.RpcError as e:
        code = e.code()
        if code == StatusCode.NOT_FOUND:
            raise LookupError(e.details())
        raise


def validate_token(token):
    block_business_grpc('__init__.py.validate_token')
    stub = auth_pb2_grpc.AuthServiceStub(auth_channel())
    req = auth_pb2.ValidateTokenRequest(
        credential=agm_common_pb2.AccessTokenCredential(access_token=token),
    )
    try:
        return stub.ValidateToken(req, timeout=TIMEOUT)
    except grpc.RpcError as e:
        code = e.code()
        if code == StatusCode.UNAUTHENTICATED:
            raise PermissionError(e.details())
        raise


def get_materia_by_id(materia_id):
    block_business_grpc('__init__.py.get_materia_by_id')
    stub = periodos_pb2_grpc.PeriodosServiceStub(periodos_channel())
    req = periodos_pb2.GetMateriaByIdRequest(materia_id=materia_id)
    try:
        return stub.GetMateriaById(req, timeout=TIMEOUT)
    except grpc.RpcError as e:
        code = e.code()
        if code == StatusCode.NOT_FOUND:
            raise LookupError(e.details())
        raise


def get_alumnos_by_materia(materia_id):
    block_business_grpc('__init__.py.get_alumnos_by_materia')
    stub = alumnos_pb2_grpc.AlumnosServiceStub(alumnos_channel())
    req = alumnos_pb2.GetAlumnosByMateriaRequest(materia_id=materia_id)
    try:
        return stub.GetAlumnosByMateria(req, timeout=TIMEOUT)
    except grpc.RpcError as e:
        code = e.code()
        if code == StatusCode.NOT_FOUND:
            raise LookupError(e.details())
        raise


def is_alumno_en_materia(alumno_id, materia_id):
    block_business_grpc('__init__.py.is_alumno_en_materia')
    """
    Verifica si un alumno está inscrito activo en una materia (via MS-3).
    Retorna bool; raise LookupError si no está encontrado.
    """
    stub = alumnos_pb2_grpc.AlumnosServiceStub(alumnos_channel())
    req = alumnos_pb2.IsAlumnoEnMateriaRequest(alumno_id=alumno_id, materia_id=materia_id)
    try:
        resp = stub.IsAlumnoEnMateria(req, timeout=TIMEOUT)
        return resp.inscrito
    except grpc.RpcError as e:
        code = e.code()
        if code == StatusCode.NOT_FOUND:
            raise LookupError(e.details())
        raise


__all__ = [
    'alumnos_channel',
    'auth_channel',
    'periodos_channel',
    'get_alumno_by_id',
    'validate_token',
    'get_materia_by_id',
    'get_alumnos_by_materia',
    'is_alumno_en_materia',
]
