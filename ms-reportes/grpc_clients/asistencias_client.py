import grpc

from config.agm_env import env_bool
from grpc_clients.channel import get_channel, grpc_timeout
from grpc_clients.exceptions import map_rpc_error
from grpc_clients.mocks import mock_asistencia_alumno, mock_estadisticas_asistencia
from proto_generated import asistencias_pb2, asistencias_pb2_grpc

"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""
from agm_events.grpc_legacy import block_business_grpc

_SERVICE = 'ms-asistencias'

_FALLBACK_CODES = frozenset(
    {
        grpc.StatusCode.UNAVAILABLE,
        grpc.StatusCode.DEADLINE_EXCEEDED,
        grpc.StatusCode.UNIMPLEMENTED,
        grpc.StatusCode.UNKNOWN,
    }
)


def use_mock_data() -> bool:
    return env_bool('USE_MOCK_DATA', default=False)


def _should_fallback_to_mock(exc: grpc.RpcError) -> bool:
    return exc.code() in _FALLBACK_CODES


def get_asistencias_stub() -> asistencias_pb2_grpc.AsistenciasServiceStub:
    block_business_grpc('asistencias_client.py.get_asistencias_stub')
    channel = get_channel(
        'asistencias',
        'MS_ASISTENCIAS_GRPC_HOST',
        'MS_ASISTENCIAS_GRPC_PORT',
        'ms-asistencias',
        '50055',
    )
    return asistencias_pb2_grpc.AsistenciasServiceStub(channel)


def get_asistencia_alumno(alumno_id: int, materia_id: int) -> asistencias_pb2.AsistenciaAlumnoResponse:
    block_business_grpc('asistencias_client.py.get_asistencia_alumno')
    if use_mock_data():
        return mock_asistencia_alumno(alumno_id, materia_id)
    try:
        return get_asistencias_stub().GetAsistenciaAlumno(
            asistencias_pb2.GetAsistenciaAlumnoRequest(
                alumno_id=alumno_id,
                materia_id=materia_id,
            ),
            timeout=grpc_timeout(),
        )
    except grpc.RpcError as exc:
        if _should_fallback_to_mock(exc):
            return mock_asistencia_alumno(alumno_id, materia_id)
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            from grpc_clients.exceptions import AlumnoNotFound
            raise AlumnoNotFound(alumno_id, exc.details() or None) from exc
        map_rpc_error(exc, _SERVICE, entity='alumno', entity_id=alumno_id)


def get_estadisticas_asistencia(materia_id: int) -> asistencias_pb2.EstadisticasAsistenciaResponse:
    block_business_grpc('asistencias_client.py.get_estadisticas_asistencia')
    """GetEstadisticasAsistencia con fallback a mock si USE_MOCK_DATA o MS-5 no responde."""
    if use_mock_data():
        return mock_estadisticas_asistencia(materia_id)
    try:
        return get_asistencias_stub().GetEstadisticasAsistencia(
            asistencias_pb2.GetEstadisticasAsistenciaRequest(materia_id=materia_id),
            timeout=grpc_timeout(),
        )
    except grpc.RpcError as exc:
        if _should_fallback_to_mock(exc):
            return mock_estadisticas_asistencia(materia_id)
        map_rpc_error(exc, _SERVICE, entity='materia', entity_id=materia_id)
