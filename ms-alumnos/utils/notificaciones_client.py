import grpc
import logging
from proto_generated import notificaciones_pb2, notificaciones_pb2_grpc

logger = logging.getLogger(__name__)

def send_bienvenida(alumno):
    """
    Envía notificación de bienvenida al alumno vía gRPC a MS-6.
    """
    try:
        # En el entorno Docker, el host es el nombre del servicio
        target = 'agm-ms-notificaciones:50056'
        
        with grpc.insecure_channel(target) as channel:
            stub = notificaciones_pb2_grpc.NotificacionesServiceStub(channel)
            
            # Según notificaciones.proto:
            # message SendBienvenidaRequest {
            #   int32 alumno_id = 1;
            #   int32 materia_id = 2;
            #   string clave_acceso = 3;
            # }
            request = notificaciones_pb2.SendBienvenidaRequest(
                alumno_id=alumno.id,
                materia_id=0,            # 0 = Bienvenida institucional (no ligada a materia)
                clave_acceso="BUAP-2026" # Clave temporal (en el futuro vendría de MS-1)
            )
            
            response = stub.SendBienvenida(request, timeout=3.0)
            return response.success
            
    except grpc.RpcError as e:
        # Loguear warning pero NO abortar el flujo principal (requerimiento)
        logger.warning(f"MS-6 no disponible o error RPC al notificar alumno {alumno.matricula}: {e.code()}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al llamar a MS-6: {str(e)}")
        return False

def send_baja_notif(inscripcion, docente_email=None):
    """
    Notifica al docente que un alumno se dio de baja de su materia vía gRPC a MS-6.
    """
    try:
        target = 'agm-ms-notificaciones:50056'
        
        with grpc.insecure_channel(target) as channel:
            stub = notificaciones_pb2_grpc.NotificacionesServiceStub(channel)
            
            # Según notificaciones.proto:
            # message SendBajaRequest {
            #   int32 alumno_id = 1;
            #   int32 docente_id = 2;
            #   int32 materia_id = 3;
            # }
            request = notificaciones_pb2.SendBajaRequest(
                alumno_id=inscripcion.alumno.id,
                docente_id=0, # Placeholder hasta ISSUE-201
                materia_id=inscripcion.materia_id
            )
            
            response = stub.SendBajaNotif(request, timeout=3.0)
            return response.success
            
    except grpc.RpcError as e:
        logger.warning(f"Error gRPC al notificar baja de {inscripcion.alumno.matricula} en materia {inscripcion.materia_id}: {e.code()}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al notificar baja: {str(e)}")
        return False
