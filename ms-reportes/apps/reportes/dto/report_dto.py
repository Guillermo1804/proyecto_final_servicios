from dataclasses import dataclass


@dataclass(frozen=True)
class MateriaEncabezadoDTO:
    materia_id: int
    nrc: str
    nombre: str
    seccion: str
    clave: str
    docente_nombre: str
    docente_id: int
    periodo_id: int
    periodo_nombre: str
    horario: str


@dataclass(frozen=True)
class ActividadCalificacionDTO:
    actividad_id: int
    actividad_nombre: str
    categoria: str
    calificacion: float


@dataclass(frozen=True)
class ActividadColumnaDTO:
    actividad_id: int
    nombre: str


@dataclass(frozen=True)
class CategoriaConcentradoDTO:
    nombre: str
    porcentaje: float
    actividades: tuple[ActividadColumnaDTO, ...]


@dataclass(frozen=True)
class AlumnoCalificacionRowDTO:
    alumno_id: int
    matricula: str
    nombre: str
    calificaciones: tuple[ActividadCalificacionDTO, ...]
    promedio_real: float
    promedio_redondeado: int


@dataclass(frozen=True)
class CalificacionesReportDTO:
    materia: MateriaEncabezadoDTO
    categorias: tuple[CategoriaConcentradoDTO, ...]
    alumnos: tuple[AlumnoCalificacionRowDTO, ...]


@dataclass(frozen=True)
class AlumnoAsistenciaRowDTO:
    alumno_id: int
    matricula: str
    nombre: str
    presentes: int
    retardos: int
    ausentes: int
    porcentaje_asistencia: float


@dataclass(frozen=True)
class AsistenciasReportDTO:
    materia: MateriaEncabezadoDTO
    total_sesiones: int
    porcentaje_asistencia_grupal: float
    alumnos: tuple[AlumnoAsistenciaRowDTO, ...]


@dataclass(frozen=True)
class StatsPeriodoDTO:
    periodo_nombre: str
    periodo_id: int
    materia_nombre: str
    materia_id: int
    total_alumnos: int
    aprobados: int
    reprobados: int
    promedio_grupal: float
    porcentaje_asistencia: float


@dataclass(frozen=True)
class MateriaAlumnoStatsDTO:
    materia_id: int
    materia_nombre: str
    periodo_nombre: str
    promedio_real: float
    promedio_redondeado: int
    total_sesiones: int
    presentes: int
    retardos: int
    ausentes: int
    porcentaje_asistencia: float


@dataclass(frozen=True)
class AlumnoStatsDTO:
    alumno_id: int
    matricula: str
    nombre: str
    email: str
    materias: tuple[MateriaAlumnoStatsDTO, ...]
