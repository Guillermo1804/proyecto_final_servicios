import grpc

from apps.notificaciones.exceptions import (
    AlumnoNotFound,
    DocenteNotFound,
    MateriaNotFound,
    UpstreamGrpcError,
    UpstreamUnavailable,
)


def map_rpc_error(exc: grpc.RpcError, service: str, *, entity: str, entity_id: int) -> None:
    code = exc.code()
    details = exc.details() or ''

    if code == grpc.StatusCode.NOT_FOUND:
        if entity == 'alumno':
            raise AlumnoNotFound(entity_id, details or None) from exc
        if entity == 'docente':
            raise DocenteNotFound(entity_id, details or None) from exc
        if entity == 'materia':
            raise MateriaNotFound(entity_id, details or None) from exc

    if code == grpc.StatusCode.DEADLINE_EXCEEDED:
        raise UpstreamUnavailable(service, f'Timeout al contactar {service}') from exc

    raise UpstreamGrpcError(service, code.name, details) from exc
