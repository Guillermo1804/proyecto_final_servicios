import grpc
from django.db.models import Count, Q

from apps.core.models import RegistroAsistencia, SesionAsistencia
from grpc_clients import get_alumno_by_id
from proto_generated import asistencias_pb2, asistencias_pb2_grpc


def _safe_percentage(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


class AsistenciasServicer(asistencias_pb2_grpc.AsistenciasServiceServicer):
    """Implementacion gRPC para consultas de asistencia consumidas por MS-7."""

    def GetAsistenciaAlumno(self, request, context):
        """Retorna historial y resumen de asistencia de un alumno en una materia."""
        if request.alumno_id <= 0 or request.materia_id <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("alumno_id y materia_id deben ser mayores a 0")
            return asistencias_pb2.AsistenciaAlumnoResponse()

        try:
            total_sesiones = SesionAsistencia.objects.filter(
                materia_id=request.materia_id
            ).count()

            registros_qs = RegistroAsistencia.objects.filter(
                alumno_id=request.alumno_id,
                sesion__materia_id=request.materia_id,
            ).order_by("-fecha_registro")

            presentes = registros_qs.filter(estado="presente").count()
            retardos = registros_qs.filter(estado="retardo").count()
            asistidos = presentes + retardos
            ausentes = max(total_sesiones - asistidos, 0)

            registros = [
                asistencias_pb2.RegistroAsistencia(
                    fecha=registro.fecha_registro.date().isoformat(),
                    estado=registro.estado,
                    hora_registro=registro.fecha_registro.time().strftime("%H:%M:%S"),
                )
                for registro in registros_qs
            ]

            return asistencias_pb2.AsistenciaAlumnoResponse(
                alumno_id=request.alumno_id,
                materia_id=request.materia_id,
                total_sesiones=total_sesiones,
                presentes=presentes,
                retardos=retardos,
                ausentes=ausentes,
                porcentaje_asistencia=_safe_percentage(asistidos, total_sesiones),
                registros=registros,
            )
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error obteniendo asistencia de alumno: {exc}")
            return asistencias_pb2.AsistenciaAlumnoResponse()

    def GetEstadisticasAsistencia(self, request, context):
        """Retorna estadisticas agregadas de una materia y resumen por alumno."""
        if request.materia_id <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("materia_id debe ser mayor a 0")
            return asistencias_pb2.EstadisticasAsistenciaResponse()

        try:
            total_sesiones = SesionAsistencia.objects.filter(
                materia_id=request.materia_id
            ).count()

            por_alumno = (
                RegistroAsistencia.objects.filter(sesion__materia_id=request.materia_id)
                .values("alumno_id")
                .annotate(
                    presentes=Count("id", filter=Q(estado="presente")),
                    retardos=Count("id", filter=Q(estado="retardo")),
                    ausentes=Count("id", filter=Q(estado="ausente")),
                )
                .order_by("alumno_id")
            )

            alumnos = []
            total_asistidos = 0

            for row in por_alumno:
                alumno_id = int(row["alumno_id"])
                presentes = int(row["presentes"])
                retardos = int(row["retardos"])
                ausentes_reg = int(row["ausentes"])

                asistidos = presentes + retardos
                total_asistidos += asistidos

                ausentes = max(total_sesiones - asistidos, ausentes_reg)

                matricula = ""
                nombre = ""
                try:
                    alumno = get_alumno_by_id(alumno_id)
                    matricula = getattr(alumno, "matricula", "") or ""
                    nombre = getattr(alumno, "nombre", "") or ""
                except Exception:
                    # Se permite retornar IDs solamente si MS-3 no responde.
                    pass

                alumnos.append(
                    asistencias_pb2.AsistenciaAlumnoResumen(
                        alumno_id=alumno_id,
                        matricula=matricula,
                        nombre=nombre,
                        presentes=presentes,
                        retardos=retardos,
                        ausentes=ausentes,
                        porcentaje=_safe_percentage(asistidos, total_sesiones),
                    )
                )

            total_alumnos = len(alumnos)
            porcentaje_grupal = _safe_percentage(
                total_asistidos, total_sesiones * total_alumnos
            )

            return asistencias_pb2.EstadisticasAsistenciaResponse(
                materia_id=request.materia_id,
                total_sesiones=total_sesiones,
                porcentaje_asistencia_grupal=porcentaje_grupal,
                alumnos=alumnos,
            )
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error obteniendo estadisticas de asistencia: {exc}")
            return asistencias_pb2.EstadisticasAsistenciaResponse()
