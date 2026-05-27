"""Excepciones de dominio MS-7 (sin acoplar a grpc_clients legacy)."""


class ReportesDomainError(Exception):
    """Base para errores de negocio en reportes."""


class AlumnoNotFound(ReportesDomainError):
    def __init__(self, alumno_id: int, message: str | None = None):
        self.alumno_id = alumno_id
        super().__init__(message or f'Alumno {alumno_id} no encontrado')


class MateriaNotFound(ReportesDomainError):
    def __init__(self, materia_id: int, message: str | None = None):
        self.materia_id = materia_id
        super().__init__(message or f'Materia {materia_id} no encontrada')
