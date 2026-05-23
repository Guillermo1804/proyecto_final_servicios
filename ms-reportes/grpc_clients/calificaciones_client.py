import grpc

from config.agm_env import env_bool
from grpc_clients.channel import calificaciones_grpc_timeout, get_channel
from grpc_clients.exceptions import map_rpc_error
from grpc_clients.mocks import mock_concentrado
from proto_generated import calificaciones_pb2, calificaciones_pb2_grpc

"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""
from agm_events.grpc_legacy import block_business_grpc

_SERVICE = 'ms-calificaciones'

_FALLBACK_CODES = frozenset(
    {
        grpc.StatusCode.UNAVAILABLE,
        grpc.StatusCode.DEADLINE_EXCEEDED,
        grpc.StatusCode.UNIMPLEMENTED,
        grpc.StatusCode.UNKNOWN,
    }
)


def use_mock_data() -> bool:
    block_business_grpc('calificaciones_client.py.use_mock_data')
    return env_bool('USE_MOCK_DATA', default=False)


def _should_fallback_to_mock(exc: grpc.RpcError) -> bool:
    block_business_grpc('calificaciones_client.py._should_fallback_to_mock')
    return exc.code() in _FALLBACK_CODES


def _mock_estadisticas_materia(materia_id: int) -> calificaciones_pb2.EstadisticasMateriaResponse:
    block_business_grpc('calificaciones_client.py._mock_estadisticas_materia')
    concentrado = mock_concentrado(materia_id)
    aprobados = sum(1 for a in concentrado.alumnos if a.promedio_redondeado >= 6)
    reprobados = len(concentrado.alumnos) - aprobados
    promedios = [a.promedio_real for a in concentrado.alumnos] or [0.0]
    return calificaciones_pb2.EstadisticasMateriaResponse(
        total_alumnos=len(concentrado.alumnos),
        aprobados=aprobados,
        reprobados=reprobados,
        promedio_grupal=sum(promedios) / len(promedios),
        calificacion_maxima=max(promedios),
        calificacion_minima=min(promedios),
    )


def get_calificaciones_stub() -> calificaciones_pb2_grpc.CalificacionesServiceStub:
    block_business_grpc('calificaciones_client.py.get_calificaciones_stub')
    channel = get_channel(
        'calificaciones',
        'MS_CALIFICACIONES_GRPC_HOST',
        'MS_CALIFICACIONES_GRPC_PORT',
        'ms-calificaciones',
        '50054',
    )
    return calificaciones_pb2_grpc.CalificacionesServiceStub(channel)


def get_concentrado(materia_id: int) -> calificaciones_pb2.ConcentradoResponse:
    block_business_grpc('calificaciones_client.py.get_concentrado')
    """GetConcentrado con fallback a mock si USE_MOCK_DATA o MS-4 no responde."""
    if use_mock_data():
        return mock_concentrado(materia_id)
    try:
        return get_calificaciones_stub().GetConcentrado(
            calificaciones_pb2.GetConcentradoRequest(materia_id=materia_id),
            timeout=calificaciones_grpc_timeout(),
        )
    except grpc.RpcError as exc:
        if _should_fallback_to_mock(exc):
            return mock_concentrado(materia_id)
        map_rpc_error(exc, _SERVICE, entity='materia', entity_id=materia_id)


def get_estadisticas_materia(materia_id: int) -> calificaciones_pb2.EstadisticasMateriaResponse:
    block_business_grpc('calificaciones_client.py.get_estadisticas_materia')
    if use_mock_data():
        return _mock_estadisticas_materia(materia_id)
    try:
        return get_calificaciones_stub().GetEstadisticasMateria(
            calificaciones_pb2.GetEstadisticasMateriaRequest(materia_id=materia_id),
            timeout=calificaciones_grpc_timeout(),
        )
    except grpc.RpcError as exc:
        if _should_fallback_to_mock(exc):
            return _mock_estadisticas_materia(materia_id)
        map_rpc_error(exc, _SERVICE, entity='materia', entity_id=materia_id)


def get_promedio_alumno(alumno_id: int, materia_id: int) -> calificaciones_pb2.PromedioResponse:
    block_business_grpc('calificaciones_client.py.get_promedio_alumno')
    if use_mock_data():
        concentrado = mock_concentrado(materia_id)
        for alumno in concentrado.alumnos:
            if alumno.alumno_id == alumno_id:
                return calificaciones_pb2.PromedioResponse(
                    promedio_real=alumno.promedio_real,
                    promedio_redondeado=alumno.promedio_redondeado,
                )
        from grpc_clients.exceptions import AlumnoNotFound
        raise AlumnoNotFound(alumno_id)
    try:
        return get_calificaciones_stub().GetPromedioAlumno(
            calificaciones_pb2.GetPromedioAlumnoRequest(
                alumno_id=alumno_id,
                materia_id=materia_id,
            ),
            timeout=calificaciones_grpc_timeout(),
        )
    except grpc.RpcError as exc:
        if _should_fallback_to_mock(exc):
            concentrado = mock_concentrado(materia_id)
            for alumno in concentrado.alumnos:
                if alumno.alumno_id == alumno_id:
                    return calificaciones_pb2.PromedioResponse(
                        promedio_real=alumno.promedio_real,
                        promedio_redondeado=alumno.promedio_redondeado,
                    )
            from grpc_clients.exceptions import AlumnoNotFound
            raise AlumnoNotFound(alumno_id)
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            from grpc_clients.exceptions import AlumnoNotFound
            raise AlumnoNotFound(alumno_id, exc.details() or None) from exc
        map_rpc_error(exc, _SERVICE, entity='materia', entity_id=materia_id)
