"""Excepciones de dominio para errores upstream (MS-7)."""

import grpc


class ReportesDomainError(Exception):
    """Base para errores de negocio en capa gRPC saliente."""


class AlumnoNotFound(ReportesDomainError):
    def __init__(self, alumno_id: int, message: str | None = None):
        self.alumno_id = alumno_id
        super().__init__(message or f'Alumno {alumno_id} no encontrado')


class MateriaNotFound(ReportesDomainError):
    def __init__(self, materia_id: int, message: str | None = None):
        self.materia_id = materia_id
        super().__init__(message or f'Materia {materia_id} no encontrada')


class PermissionDenied(ReportesDomainError):
    def __init__(self, message: str | None = None):
        super().__init__(message or 'Permiso denegado')


class UpstreamUnavailable(ReportesDomainError):
    """MS upstream no respondió o no está disponible."""

    def __init__(self, service: str, message: str | None = None):
        self.service = service
        super().__init__(message or f'Servicio {service} no disponible')


class UpstreamGrpcError(ReportesDomainError):
    """Error gRPC no mapeado a dominio."""

    def __init__(self, service: str, code: str, details: str = ''):
        self.service = service
        self.code = code
        self.details = details
        super().__init__(f'{service} gRPC {code}: {details}')


def map_rpc_error(exc: grpc.RpcError, service: str, *, entity: str, entity_id: int) -> None:
    """Traduce códigos gRPC a excepciones de dominio."""
    code = exc.code()
    details = exc.details() or ''

    if code == grpc.StatusCode.NOT_FOUND:
        if entity == 'alumno':
            raise AlumnoNotFound(entity_id, details or None) from exc
        if entity == 'materia':
            raise MateriaNotFound(entity_id, details or None) from exc

    if code == grpc.StatusCode.PERMISSION_DENIED:
        raise PermissionDenied(details or 'Permiso denegado') from exc

    if code in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
        raise UpstreamUnavailable(service, details or f'No se pudo contactar {service}') from exc

    raise UpstreamGrpcError(service, code.name, details) from exc
