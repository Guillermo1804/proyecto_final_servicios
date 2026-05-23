"""Agregación de estadísticas JSON desde proyecciones locales (sin gRPC)."""

from __future__ import annotations

from apps.reportes.dto.report_dto import AlumnoStatsDTO, MateriaAlumnoStatsDTO, StatsPeriodoDTO
from apps.reportes.models import ReporteAlumnoProjection, ReporteMateriaProjection
from apps.reportes.services.analytics_state import get_data_as_of

from apps.reportes.exceptions import AlumnoNotFound


class EstadisticasService:
    """Consolida métricas desde read models db-reportes."""

    def historial_docente(self, usuario_id: int) -> tuple[StatsPeriodoDTO, ...]:
        materias = ReporteMateriaProjection.objects.filter(docente_id=usuario_id).order_by(
            'periodo_id',
            'nombre',
        )
        periodos: list[StatsPeriodoDTO] = []
        for materia in materias:
            periodos.append(
                StatsPeriodoDTO(
                    periodo_nombre=materia.periodo_nombre,
                    periodo_id=materia.periodo_id,
                    materia_nombre=materia.nombre,
                    materia_id=materia.materia_id,
                    total_alumnos=materia.total_alumnos,
                    aprobados=materia.aprobados,
                    reprobados=materia.reprobados,
                    promedio_grupal=float(materia.promedio_grupal),
                    porcentaje_asistencia=float(materia.porcentaje_asistencia_grupal),
                )
            )
        return tuple(periodos)

    def stats_alumno(self, alumno_id: int) -> AlumnoStatsDTO:
        inscripciones = ReporteAlumnoProjection.objects.filter(
            alumno_id=alumno_id,
            activa=True,
        ).order_by('materia_id')
        if not inscripciones.exists():
            raise AlumnoNotFound(alumno_id)

        first = inscripciones.first()
        materias_stats: list[MateriaAlumnoStatsDTO] = []
        for ins in inscripciones:
            materia = ReporteMateriaProjection.objects.filter(materia_id=ins.materia_id).first()
            materias_stats.append(
                MateriaAlumnoStatsDTO(
                    materia_id=ins.materia_id,
                    materia_nombre=materia.nombre if materia else '',
                    periodo_nombre=materia.periodo_nombre if materia else '',
                    promedio_real=float(ins.promedio_real),
                    promedio_redondeado=int(ins.promedio_redondeado),
                    total_sesiones=materia.total_sesiones_qr if materia else 0,
                    presentes=ins.presentes,
                    retardos=ins.retardos,
                    ausentes=ins.ausentes,
                    porcentaje_asistencia=float(ins.porcentaje_asistencia),
                )
            )

        return AlumnoStatsDTO(
            alumno_id=alumno_id,
            matricula=first.matricula,
            nombre=first.nombre,
            email=first.email,
            materias=tuple(materias_stats),
        )

    @staticmethod
    def data_as_of():
        return get_data_as_of()
