"""Consultas analíticas exclusivamente sobre proyecciones locales db-reportes."""

from __future__ import annotations

from collections import defaultdict
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
from apps.reportes.models import (
    ReporteAlumnoProjection,
    ReporteCalificacionProjection,
    ReporteMateriaProjection,
)
from apps.reportes.services.analytics_state import get_data_as_of

from apps.reportes.exceptions import MateriaNotFound


class ReportDataService:
    """Fuente única de datos para generadores Excel/PDF (sin gRPC upstream)."""

    def fetch_calificaciones(self, materia_id: int) -> CalificacionesReportDTO:
        materia = _get_materia_or_404(materia_id)
        alumnos_qs = ReporteAlumnoProjection.objects.filter(
            materia_id=materia_id,
            activa=True,
        ).order_by('matricula')
        califs = ReporteCalificacionProjection.objects.filter(materia_id=materia_id)

        categorias = _build_categorias(califs)
        calif_by_alumno: dict[int, list[ReporteCalificacionProjection]] = defaultdict(list)
        for row in califs:
            if row.calificacion is not None:
                calif_by_alumno[row.alumno_id].append(row)

        filas: list[AlumnoCalificacionRowDTO] = []
        for alumno in alumnos_qs:
            grades = calif_by_alumno.get(alumno.alumno_id, [])
            filas.append(
                AlumnoCalificacionRowDTO(
                    alumno_id=alumno.alumno_id,
                    matricula=alumno.matricula,
                    nombre=alumno.nombre,
                    calificaciones=tuple(
                        ActividadCalificacionDTO(
                            actividad_id=g.actividad_id,
                            actividad_nombre=g.actividad_nombre,
                            categoria=g.categoria,
                            calificacion=float(g.calificacion),
                        )
                        for g in grades
                    ),
                    promedio_real=float(alumno.promedio_real),
                    promedio_redondeado=int(alumno.promedio_redondeado),
                )
            )

        return CalificacionesReportDTO(
            materia=_materia_dto(materia),
            categorias=categorias,
            alumnos=tuple(filas),
            data_as_of=get_data_as_of(),
        )

    def fetch_asistencias(self, materia_id: int) -> AsistenciasReportDTO:
        materia = _get_materia_or_404(materia_id)
        alumnos_qs = ReporteAlumnoProjection.objects.filter(
            materia_id=materia_id,
            activa=True,
        ).order_by('matricula')

        filas = tuple(
            AlumnoAsistenciaRowDTO(
                alumno_id=a.alumno_id,
                matricula=a.matricula,
                nombre=a.nombre,
                presentes=a.presentes,
                retardos=a.retardos,
                ausentes=a.ausentes,
                porcentaje_asistencia=float(a.porcentaje_asistencia),
            )
            for a in alumnos_qs
        )

        return AsistenciasReportDTO(
            materia=_materia_dto(materia),
            total_sesiones=materia.total_sesiones_qr,
            porcentaje_asistencia_grupal=float(materia.porcentaje_asistencia_grupal),
            alumnos=filas,
            data_as_of=get_data_as_of(),
        )


def _get_materia_or_404(materia_id: int) -> ReporteMateriaProjection:
    materia = ReporteMateriaProjection.objects.filter(materia_id=materia_id).first()
    if materia is None:
        raise MateriaNotFound(materia_id)
    return materia


def _materia_dto(materia: ReporteMateriaProjection) -> MateriaEncabezadoDTO:
    return MateriaEncabezadoDTO(
        materia_id=materia.materia_id,
        nrc=materia.nrc,
        nombre=materia.nombre,
        seccion=materia.seccion,
        clave=materia.clave,
        docente_nombre=materia.docente_nombre,
        docente_id=materia.docente_id or 0,
        periodo_id=materia.periodo_id,
        periodo_nombre=materia.periodo_nombre,
        horario=materia.horario,
    )


def _build_categorias(
    califs,
) -> tuple[CategoriaConcentradoDTO, ...]:
    by_cat: dict[str, dict] = {}
    for row in califs:
        cat = row.categoria or 'General'
        if cat not in by_cat:
            by_cat[cat] = {
                'porcentaje': float(row.porcentaje_categoria or 0),
                'actividades': {},
            }
        by_cat[cat]['actividades'][row.actividad_id] = row.actividad_nombre

    categorias: list[CategoriaConcentradoDTO] = []
    for nombre, data in sorted(by_cat.items()):
        acts = tuple(
            ActividadColumnaDTO(actividad_id=aid, nombre=aname)
            for aid, aname in sorted(data['actividades'].items())
        )
        categorias.append(
            CategoriaConcentradoDTO(
                nombre=nombre,
                porcentaje=data['porcentaje'],
                actividades=acts,
            )
        )
    return tuple(categorias)
