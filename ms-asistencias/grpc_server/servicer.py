import grpc
from proto_generated import asistencias_pb2, asistencias_pb2_grpc


class AsistenciasServicer(asistencias_pb2_grpc.AsistenciasServiceServicer):
    """Implementación mínima de RPCs para MS-5."""

    def GetAsistenciaAlumno(self, request, context):
        return asistencias_pb2.AsistenciaAlumnoResponse(
            alumno_id=request.alumno_id,
            materia_id=request.materia_id,
            total_sesiones=0,
            presentes=0,
            retardos=0,
            ausentes=0,
            porcentaje_asistencia=0.0,
            registros=[],
        )

    def GetEstadisticasAsistencia(self, request, context):
        return asistencias_pb2.EstadisticasAsistenciaResponse(
            materia_id=request.materia_id,
            total_sesiones=0,
            porcentaje_asistencia_grupal=0.0,
            alumnos=[],
        )
