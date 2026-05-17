"""Respuestas gRPC estáticas para desarrollo sin MS-4 / MS-5."""

from proto_generated import asistencias_pb2, calificaciones_pb2


def mock_concentrado(materia_id: int) -> calificaciones_pb2.ConcentradoResponse:
    categoria = calificaciones_pb2.CategoriaConcentrado(
        nombre='Exámenes',
        porcentaje=40.0,
        actividades=[
            calificaciones_pb2.ActividadInfo(id=1, nombre='Parcial 1'),
            calificaciones_pb2.ActividadInfo(id=2, nombre='Parcial 2'),
        ],
    )
    return calificaciones_pb2.ConcentradoResponse(
        materia_id=materia_id,
        categorias=[categoria],
        alumnos=[
            calificaciones_pb2.AlumnoCalificacion(
                alumno_id=1,
                matricula='20240001',
                nombre='Ana García López',
                promedio_real=7.65,
                promedio_redondeado=8,
                calificaciones=[
                    calificaciones_pb2.CalificacionActividad(
                        actividad_id=1,
                        actividad_nombre='Parcial 1',
                        categoria='Exámenes',
                        calificacion=8.0,
                    ),
                    calificaciones_pb2.CalificacionActividad(
                        actividad_id=2,
                        actividad_nombre='Parcial 2',
                        categoria='Exámenes',
                        calificacion=7.3,
                    ),
                ],
            ),
            calificaciones_pb2.AlumnoCalificacion(
                alumno_id=2,
                matricula='20240002',
                nombre='Luis Martínez',
                promedio_real=5.45,
                promedio_redondeado=5,
                calificaciones=[
                    calificaciones_pb2.CalificacionActividad(
                        actividad_id=1,
                        actividad_nombre='Parcial 1',
                        categoria='Exámenes',
                        calificacion=5.0,
                    ),
                ],
            ),
        ],
    )


def mock_asistencia_alumno(alumno_id: int, materia_id: int) -> asistencias_pb2.AsistenciaAlumnoResponse:
    stats = mock_estadisticas_asistencia(materia_id)
    for resumen in stats.alumnos:
        if resumen.alumno_id == alumno_id:
            return asistencias_pb2.AsistenciaAlumnoResponse(
                alumno_id=alumno_id,
                materia_id=materia_id,
                total_sesiones=stats.total_sesiones,
                presentes=resumen.presentes,
                retardos=resumen.retardos,
                ausentes=resumen.ausentes,
                porcentaje_asistencia=resumen.porcentaje,
                registros=[],
            )
    return asistencias_pb2.AsistenciaAlumnoResponse(
        alumno_id=alumno_id,
        materia_id=materia_id,
        total_sesiones=stats.total_sesiones,
        presentes=0,
        retardos=0,
        ausentes=stats.total_sesiones,
        porcentaje_asistencia=0.0,
        registros=[],
    )


def mock_estadisticas_asistencia(materia_id: int) -> asistencias_pb2.EstadisticasAsistenciaResponse:
    return asistencias_pb2.EstadisticasAsistenciaResponse(
        materia_id=materia_id,
        total_sesiones=10,
        porcentaje_asistencia_grupal=82.5,
        alumnos=[
            asistencias_pb2.AsistenciaAlumnoResumen(
                alumno_id=1,
                matricula='20240001',
                nombre='Ana García López',
                presentes=9,
                retardos=1,
                ausentes=0,
                porcentaje=90.0,
            ),
            asistencias_pb2.AsistenciaAlumnoResumen(
                alumno_id=2,
                matricula='20240002',
                nombre='Luis Martínez',
                presentes=7,
                retardos=0,
                ausentes=3,
                porcentaje=70.0,
            ),
        ],
    )
