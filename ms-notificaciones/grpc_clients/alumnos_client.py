import grpc

from grpc_clients.channel import get_channel, grpc_timeout
from grpc_clients.errors import map_rpc_error
from proto_generated import alumnos_pb2, alumnos_pb2_grpc

"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""
from agm_events.grpc_legacy import block_business_grpc


def get_alumnos_stub() -> alumnos_pb2_grpc.AlumnosServiceStub:
    block_business_grpc('alumnos_client.py.get_alumnos_stub')
    channel = get_channel(
        'alumnos',
        'MS_ALUMNOS_GRPC_HOST',
        'MS_ALUMNOS_GRPC_PORT',
        'ms-alumnos',
        '50053',
    )
    return alumnos_pb2_grpc.AlumnosServiceStub(channel)


def get_alumno_by_id(alumno_id: int) -> alumnos_pb2.AlumnoInfo:
    block_business_grpc('alumnos_client.py.get_alumno_by_id')
    try:
        return get_alumnos_stub().GetAlumnoById(
            alumnos_pb2.GetAlumnoByIdRequest(alumno_id=alumno_id),
            timeout=grpc_timeout(),
        )
    except grpc.RpcError as exc:
        map_rpc_error(exc, 'ms-alumnos', entity='alumno', entity_id=alumno_id)
        raise


def get_alumnos_by_materia(materia_id: int) -> alumnos_pb2.AlumnosListResponse:
    block_business_grpc('alumnos_client.py.get_alumnos_by_materia')
    try:
        return get_alumnos_stub().GetAlumnosByMateria(
            alumnos_pb2.GetAlumnosByMateriaRequest(materia_id=materia_id),
            timeout=grpc_timeout(),
        )
    except grpc.RpcError as exc:
        map_rpc_error(exc, 'ms-alumnos', entity='materia', entity_id=materia_id)
        raise


def get_docente_by_usuario_id(usuario_id: int) -> alumnos_pb2.DocenteInfo:
    block_business_grpc('alumnos_client.py.get_docente_by_usuario_id')
    try:
        return get_alumnos_stub().GetDocenteByUsuarioId(
            alumnos_pb2.GetDocenteByUsuarioIdRequest(usuario_id=usuario_id),
            timeout=grpc_timeout(),
        )
    except grpc.RpcError as exc:
        map_rpc_error(exc, 'ms-alumnos', entity='docente', entity_id=usuario_id)
        raise
