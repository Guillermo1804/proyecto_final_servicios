"""Agregación de estadísticas JSON (docente / alumno)."""

from decouple import config

from grpc_clients import alumnos_client, asistencias_client, calificaciones_client, periodos_client
from grpc_clients.exceptions import AlumnoNotFound
from apps.reportes.dto.report_dto import AlumnoStatsDTO, MateriaAlumnoStatsDTO, StatsPeriodoDTO


class EstadisticasService:
    """Consolida métricas de MS-2…MS-5 sin recalcular promedios de calificación."""

    def historial_docente(self, usuario_id: int) -> tuple[StatsPeriodoDTO, ...]:
        """
        Resumen por materia del docente (usuario_id = docente_id en MS-2).

        aprobados / reprobados / promedio_grupal provienen de MS-4 GetEstadisticasMateria.
        """
        materias = periodos_client.get_materias_by_docente(usuario_id)
        periodos: list[StatsPeriodoDTO] = []

        for materia in materias.materias:
            stats_cal = calificaciones_client.get_estadisticas_materia(materia.id)
            stats_asi = asistencias_client.get_estadisticas_asistencia(materia.id)
            periodos.append(
                StatsPeriodoDTO(
                    periodo_nombre=materia.periodo_nombre,
                    periodo_id=materia.periodo_id,
                    materia_nombre=materia.nombre,
                    materia_id=materia.id,
                    total_alumnos=stats_cal.total_alumnos,
                    aprobados=stats_cal.aprobados,
                    reprobados=stats_cal.reprobados,
                    promedio_grupal=stats_cal.promedio_grupal,
                    porcentaje_asistencia=stats_asi.porcentaje_asistencia_grupal,
                )
            )

        periodos.sort(key=lambda p: (p.periodo_id, p.materia_nombre))
        return tuple(periodos)

    def stats_alumno(self, alumno_id: int) -> AlumnoStatsDTO:
        """Historial académico individual por materia (promedios MS-4, asistencia MS-5)."""
        alumno = alumnos_client.get_alumno_by_id(alumno_id)
        materia_ids = _materia_ids_para_alumno(alumno_id)
        materias_stats: list[MateriaAlumnoStatsDTO] = []

        for materia_id in materia_ids:
            try:
                materia = periodos_client.get_materia_by_id(materia_id)
                promedio = calificaciones_client.get_promedio_alumno(alumno_id, materia_id)
                asistencia = asistencias_client.get_asistencia_alumno(alumno_id, materia_id)
            except AlumnoNotFound:
                continue

            materias_stats.append(
                MateriaAlumnoStatsDTO(
                    materia_id=materia.id,
                    materia_nombre=materia.nombre,
                    periodo_nombre=materia.periodo_nombre,
                    promedio_real=promedio.promedio_real,
                    promedio_redondeado=promedio.promedio_redondeado,
                    total_sesiones=asistencia.total_sesiones,
                    presentes=asistencia.presentes,
                    retardos=asistencia.retardos,
                    ausentes=asistencia.ausentes,
                    porcentaje_asistencia=asistencia.porcentaje_asistencia,
                )
            )

        materias_stats.sort(key=lambda m: m.materia_nombre)
        return AlumnoStatsDTO(
            alumno_id=alumno.id,
            matricula=alumno.matricula,
            nombre=alumno.nombre,
            email=alumno.email,
            materias=tuple(materias_stats),
        )


def _materia_ids_para_alumno(alumno_id: int) -> list[int]:
    """
    MS-3 no expone listado de materias por alumno vía gRPC.
    En desarrollo se usa STATS_ALUMNO_MATERIA_IDS; con mock se infiere materia 1.
    """
    raw = config('STATS_ALUMNO_MATERIA_IDS', default='')
    if raw.strip():
        return [int(x.strip()) for x in raw.split(',') if x.strip()]

    from grpc_clients.calificaciones_client import use_mock_data
    from grpc_clients.mocks import mock_concentrado

    if use_mock_data():
        materia_id = 1
        concentrado = mock_concentrado(materia_id)
        if any(a.alumno_id == alumno_id for a in concentrado.alumnos):
            return [materia_id]
    return []
