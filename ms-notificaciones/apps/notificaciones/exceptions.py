"""Excepciones de dominio para errores upstream (Fase C)."""


class NotificacionesDomainError(Exception):
    """Base para errores de negocio en MS-6."""


class AlumnoNotFound(NotificacionesDomainError):
    def __init__(self, alumno_id: int, message: str | None = None):
        self.alumno_id = alumno_id
        super().__init__(message or f'Alumno {alumno_id} no encontrado')


class DocenteNotFound(NotificacionesDomainError):
    def __init__(self, usuario_id: int, message: str | None = None):
        self.usuario_id = usuario_id
        super().__init__(message or f'Docente usuario_id={usuario_id} no encontrado')


class MateriaNotFound(NotificacionesDomainError):
    def __init__(self, materia_id: int, message: str | None = None):
        self.materia_id = materia_id
        super().__init__(message or f'Materia {materia_id} no encontrada')


class UpstreamUnavailable(NotificacionesDomainError):
    """MS upstream no respondió a tiempo o no está disponible."""

    def __init__(self, service: str, message: str | None = None):
        self.service = service
        super().__init__(message or f'Servicio {service} no disponible')


class UpstreamGrpcError(NotificacionesDomainError):
    """Error gRPC distinto a NOT_FOUND / DEADLINE_EXCEEDED."""

    def __init__(self, service: str, code: str, details: str = ''):
        self.service = service
        self.code = code
        self.details = details
        super().__init__(f'{service} gRPC {code}: {details}')
