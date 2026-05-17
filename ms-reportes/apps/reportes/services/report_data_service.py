"""Orquestación de datos upstream para reportes (MS-2, MS-3, MS-4, MS-5)."""

from grpc_clients import alumnos_client, asistencias_client, calificaciones_client, periodos_client
from apps.reportes.dto.report_dto import (
    ActividadCalificacionDTO,
    ActividadColumnaDTO,
    AlumnoAsistenciaRowDTO,
    AlumnoCalificacionRowDTO,
    AsistenciasReportDTO,
    CalificacionesReportDTO,
    CategoriaConcentradoDTO,
    MateriaEncabezadoDTO,
)


class ReportDataService:
    """Fuente única de datos para generadores Excel/PDF."""

    def fetch_calificaciones(self, materia_id: int) -> CalificacionesReportDTO:
        materia = periodos_client.get_materia_by_id(materia_id)
        concentrado = calificaciones_client.get_concentrado(materia_id)
        inscritos = alumnos_client.get_alumnos_by_materia(materia_id)

        alumnos_index = {a.id: a for a in inscritos.alumnos}

        categorias = tuple(
            CategoriaConcentradoDTO(
                nombre=cat.nombre,
                porcentaje=cat.porcentaje,
                actividades=tuple(
                    ActividadColumnaDTO(actividad_id=act.id, nombre=act.nombre)
                    for act in cat.actividades
                ),
            )
            for cat in concentrado.categorias
        )

        filas: list[AlumnoCalificacionRowDTO] = []
        for alumno_cal in concentrado.alumnos:
            ref = alumnos_index.get(alumno_cal.alumno_id)
            matricula = alumno_cal.matricula or (ref.matricula if ref else '')
            nombre = alumno_cal.nombre or (ref.nombre if ref else '')
            filas.append(
                AlumnoCalificacionRowDTO(
                    alumno_id=alumno_cal.alumno_id,
                    matricula=matricula,
                    nombre=nombre,
                    calificaciones=tuple(
                        ActividadCalificacionDTO(
                            actividad_id=c.actividad_id,
                            actividad_nombre=c.actividad_nombre,
                            categoria=c.categoria,
                            calificacion=c.calificacion,
                        )
                        for c in alumno_cal.calificaciones
                    ),
                    promedio_real=alumno_cal.promedio_real,
                    promedio_redondeado=alumno_cal.promedio_redondeado,
                )
            )

        filas.sort(key=lambda r: r.matricula)

        return CalificacionesReportDTO(
            materia=_materia_dto(materia),
            categorias=categorias,
            alumnos=tuple(filas),
        )

    def fetch_asistencias(self, materia_id: int) -> AsistenciasReportDTO:
        materia = periodos_client.get_materia_by_id(materia_id)
        estadisticas = asistencias_client.get_estadisticas_asistencia(materia_id)
        inscritos = alumnos_client.get_alumnos_by_materia(materia_id)

        alumnos_index = {a.id: a for a in inscritos.alumnos}
        asistencia_index = {a.alumno_id: a for a in estadisticas.alumnos}

        filas: list[AlumnoAsistenciaRowDTO] = []
        vistos: set[int] = set()

        for resumen in estadisticas.alumnos:
            ref = alumnos_index.get(resumen.alumno_id)
            filas.append(
                AlumnoAsistenciaRowDTO(
                    alumno_id=resumen.alumno_id,
                    matricula=resumen.matricula or (ref.matricula if ref else ''),
                    nombre=resumen.nombre or (ref.nombre if ref else ''),
                    presentes=resumen.presentes,
                    retardos=resumen.retardos,
                    ausentes=resumen.ausentes,
                    porcentaje_asistencia=resumen.porcentaje,
                )
            )
            vistos.add(resumen.alumno_id)

        for alumno in inscritos.alumnos:
            if alumno.id in vistos:
                continue
            filas.append(
                AlumnoAsistenciaRowDTO(
                    alumno_id=alumno.id,
                    matricula=alumno.matricula,
                    nombre=alumno.nombre,
                    presentes=0,
                    retardos=0,
                    ausentes=estadisticas.total_sesiones,
                    porcentaje_asistencia=0.0,
                )
            )

        filas.sort(key=lambda r: r.matricula)

        return AsistenciasReportDTO(
            materia=_materia_dto(materia),
            total_sesiones=estadisticas.total_sesiones,
            porcentaje_asistencia_grupal=estadisticas.porcentaje_asistencia_grupal,
            alumnos=tuple(filas),
        )


def _materia_dto(materia) -> MateriaEncabezadoDTO:
    return MateriaEncabezadoDTO(
        materia_id=materia.id,
        nrc=materia.nrc,
        nombre=materia.nombre,
        seccion=materia.seccion,
        clave=materia.clave,
        docente_nombre=materia.docente_nombre,
        docente_id=materia.docente_id,
        periodo_id=materia.periodo_id,
        periodo_nombre=materia.periodo_nombre,
        horario=materia.horario,
    )
