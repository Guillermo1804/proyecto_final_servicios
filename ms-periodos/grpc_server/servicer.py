import grpc
from proto_generated import periodos_pb2, periodos_pb2_grpc
from apps.core.models import Materia, Periodo

class PeriodosServicer(periodos_pb2_grpc.PeriodosServiceServicer):
    """Implementación del servicio gRPC para Periodos y Materias."""

    def GetMateriaById(self, request, context):
        try:
            m = Materia.objects.select_related("periodo").get(pk=request.materia_id)
            return periodos_pb2.MateriaInfo(
                id=m.id,
                nrc=m.nrc,
                nombre=m.nombre,
                seccion=m.seccion,
                clave=m.clave,
                docente_nombre=m.docente_nombre,
                docente_id=m.docente_id or 0,
                horario=m.horario,
                periodo_id=m.periodo.id,
                periodo_nombre=m.periodo.nombre,
            )
        except Materia.DoesNotExist:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Materia {request.materia_id} no encontrada")

    def GetMateriasByDocente(self, request, context):
        materias = Materia.objects.filter(docente_id=request.docente_id).select_related("periodo")
        res = periodos_pb2.MateriasListResponse()
        for m in materias:
            res.materias.add(
                id=m.id,
                nrc=m.nrc,
                nombre=m.nombre,
                seccion=m.seccion,
                clave=m.clave,
                docente_nombre=m.docente_nombre,
                docente_id=m.docente_id or 0,
                horario=m.horario,
                periodo_id=m.periodo.id,
                periodo_nombre=m.periodo.nombre,
            )
        return res

    def GetPeriodoActivo(self, request, context):
        try:
            p = Periodo.objects.get(activo=True)
            return periodos_pb2.PeriodoInfo(
                id=p.id,
                nombre=p.nombre,
                fecha_inicio=p.fecha_inicio.isoformat(),
                fecha_fin=p.fecha_fin.isoformat(),
                plan_estudios=p.plan_estudios,
                activo=p.activo,
            )
        except Periodo.DoesNotExist:
            context.abort(grpc.StatusCode.NOT_FOUND, "No hay periodo activo")
