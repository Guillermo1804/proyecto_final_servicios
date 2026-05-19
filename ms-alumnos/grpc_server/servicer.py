import grpc
import logging
from proto_generated import alumnos_pb2, alumnos_pb2_grpc
from apps.core.models import Alumno, Docente, InscripcionMateria

logger = logging.getLogger(__name__)

class AlumnosServicer(alumnos_pb2_grpc.AlumnosServiceServicer):
    """Implementación de los RPCs del microservicio Alumnos."""

    def GetAlumnosByMateria(self, request, context):
        """Retorna lista de alumnos inscritos y activos en una materia."""
        try:
            inscripciones = InscripcionMateria.objects.filter(
                materia_id=request.materia_id,
                activa=True
            ).select_related('alumno')
            
            response = alumnos_pb2.AlumnosListResponse()
            for insc in inscripciones:
                alumno = insc.alumno
                response.alumnos.append(alumnos_pb2.AlumnoInfo(
                    id=alumno.id,
                    usuario_id=alumno.usuario_id,
                    matricula=alumno.matricula,
                    nombre=f"{alumno.nombre} {alumno.apellido}",
                    email=alumno.email,
                    tipo_formacion=alumno.carrera
                ))
            return response
        except Exception as e:
            logger.error(f"Error en GetAlumnosByMateria: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return alumnos_pb2.AlumnosListResponse()

    def GetAlumnoById(self, request, context):
        """Retorna la información de un alumno por su ID."""
        try:
            alumno = Alumno.objects.get(id=request.alumno_id)
            return alumnos_pb2.AlumnoInfo(
                id=alumno.id,
                usuario_id=alumno.usuario_id,
                matricula=alumno.matricula,
                nombre=f"{alumno.nombre} {alumno.apellido}",
                email=alumno.email,
                tipo_formacion=alumno.carrera
            )
        except Alumno.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Alumno con ID {request.alumno_id} no encontrado")
            return alumnos_pb2.AlumnoInfo()
        except Exception as e:
            logger.error(f"Error en GetAlumnoById: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return alumnos_pb2.AlumnoInfo()

    def IsAlumnoEnMateria(self, request, context):
        """Verifica si un alumno está inscrito y activo en una materia."""
        try:
            inscrito = InscripcionMateria.objects.filter(
                alumno_id=request.alumno_id,
                materia_id=request.materia_id,
                activa=True
            ).exists()
            return alumnos_pb2.IsAlumnoEnMateriaResponse(inscrito=inscrito)
        except Exception as e:
            logger.error(f"Error en IsAlumnoEnMateria: {str(e)}")
            return alumnos_pb2.IsAlumnoEnMateriaResponse(inscrito=False)

    def GetDocenteByUsuarioId(self, request, context):
        """Busca un docente por su usuario_id de MS-1."""
        try:
            docente = Docente.objects.get(usuario_id=request.usuario_id)
            return alumnos_pb2.DocenteInfo(
                id=docente.id,
                usuario_id=docente.usuario_id,
                nombre=f"{docente.nombre} {docente.apellido}",
                email_institucional=docente.email,
                cubiculo=docente.departamento
            )
        except Docente.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Docente con usuario_id {request.usuario_id} no encontrado")
            return alumnos_pb2.DocenteInfo()
        except Exception as e:
            logger.error(f"Error en GetDocenteByUsuarioId: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return alumnos_pb2.DocenteInfo()
