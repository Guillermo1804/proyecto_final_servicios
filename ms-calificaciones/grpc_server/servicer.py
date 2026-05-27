import grpc
from proto_generated import calificaciones_pb2, calificaciones_pb2_grpc

from apps.core.models import Ponderacion
from apps.core.services import (
    calcular_promedio_ponderado,
    obtener_concentrado_materia,
    obtener_estadisticas_materia,
    redondear_institucional,
)


class CalificacionesServicer(calificaciones_pb2_grpc.CalificacionesServiceServicer):
    """Implementación mínima de RPCs para MS-4 (puede extenderse con lógica de dominio)."""

    def GetConcentrado(self, request, context):
        concentrado = obtener_concentrado_materia(request.materia_id)
        if concentrado is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('La materia no tiene datos locales.')
            return calificaciones_pb2.ConcentradoResponse(materia_id=request.materia_id)

        categorias = []
        for ponderacion, actividades in concentrado['categorias']:
            categorias.append(
                calificaciones_pb2.CategoriaConcentrado(
                    nombre=ponderacion.nombre_categoria,
                    porcentaje=float(ponderacion.porcentaje),
                    actividades=[
                        calificaciones_pb2.ActividadInfo(id=actividad.id, nombre=actividad.nombre)
                        for actividad in actividades
                    ],
                )
            )

        alumnos = []
        for alumno in concentrado['alumnos']:
            alumnos.append(
                calificaciones_pb2.AlumnoCalificacion(
                    alumno_id=alumno['alumno_id'],
                    matricula=alumno['matricula'],
                    nombre=alumno['nombre'],
                    calificaciones=[
                        calificaciones_pb2.CalificacionActividad(
                            actividad_id=item['actividad_id'],
                            actividad_nombre=item['actividad_nombre'],
                            categoria=item['categoria'],
                            calificacion=float(item['calificacion']),
                        )
                        for item in alumno['calificaciones']
                    ],
                    promedio_real=float(alumno['promedio_real']),
                    promedio_redondeado=alumno['promedio_redondeado'],
                )
            )

        return calificaciones_pb2.ConcentradoResponse(
            materia_id=request.materia_id,
            categorias=categorias,
            alumnos=alumnos,
        )

    def GetPromedioAlumno(self, request, context):
        promedio_real = calcular_promedio_ponderado(request.alumno_id, request.materia_id)
        return calificaciones_pb2.PromedioResponse(
            promedio_real=float(promedio_real),
            promedio_redondeado=redondear_institucional(promedio_real),
        )

    def GetEstadisticasMateria(self, request, context):
        estadisticas = obtener_estadisticas_materia(request.materia_id)
        if estadisticas is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('La materia no tiene datos locales.')
            return calificaciones_pb2.EstadisticasMateriaResponse()

        return calificaciones_pb2.EstadisticasMateriaResponse(
            total_alumnos=estadisticas['total_alumnos'],
            aprobados=estadisticas['aprobados'],
            reprobados=estadisticas['reprobados'],
            promedio_grupal=float(estadisticas['promedio_grupal']),
            calificacion_maxima=float(estadisticas['calificacion_maxima']),
            calificacion_minima=float(estadisticas['calificacion_minima']),
        )
