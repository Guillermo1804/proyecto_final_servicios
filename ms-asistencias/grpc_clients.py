import grpc
from decouple import config
from grpc import StatusCode

from proto_generated import alumnos_pb2_grpc, alumnos_pb2

ALUMNOS_HOST = config('MS_ALUMNOS_GRPC_HOST', default='ms-alumnos')
ALUMNOS_PORT = config('MS_ALUMNOS_GRPC_PORT', default='50053')
TIMEOUT = float(config('GRPC_CALL_TIMEOUT', default='5'))

_channel_alumnos = None


def _get_channel(host, port):
    return grpc.insecure_channel(f"{host}:{port}")


def alumnos_channel():
    global _channel_alumnos
    if _channel_alumnos is None:
        _channel_alumnos = _get_channel(ALUMNOS_HOST, ALUMNOS_PORT)
    return _channel_alumnos


def get_alumno_by_id(alumno_id):
    stub = alumnos_pb2_grpc.AlumnosServiceStub(alumnos_channel())
    req = alumnos_pb2.GetAlumnoByIdRequest(alumno_id=alumno_id)
    try:
        return stub.GetAlumnoById(req, timeout=TIMEOUT)
    except grpc.RpcError as e:
        code = e.code()
        if code == StatusCode.NOT_FOUND:
            raise LookupError(e.details())
        raise
