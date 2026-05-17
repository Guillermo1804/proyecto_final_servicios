import logging

import grpc
from decouple import config

from apps.reportes.dto.report_dto import StatsPeriodoDTO
from apps.reportes.services.estadisticas_service import EstadisticasService
from apps.reportes.services.report_data_service import ReportDataService
from apps.reportes.services.report_export import build_report_bytes, normalize_formato, normalize_tipo
from grpc_clients.exceptions import (
    AlumnoNotFound,
    MateriaNotFound,
    PermissionDenied,
    ReportesDomainError,
    UpstreamGrpcError,
    UpstreamUnavailable,
)
from proto_generated import reportes_pb2, reportes_pb2_grpc

logger = logging.getLogger(__name__)


class ReportesServicer(reportes_pb2_grpc.ReportesServiceServicer):
    """Traduce gRPC ↔ servicios de dominio (sin lógica de negocio propia)."""

    def __init__(
        self,
        report_data_service: ReportDataService | None = None,
        estadisticas_service: EstadisticasService | None = None,
    ):
        self._report_data = report_data_service or ReportDataService()
        self._estadisticas = estadisticas_service or EstadisticasService()

    def GenerateReport(self, request, context):
        if request.materia_id <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, 'materia_id debe ser mayor a 0')

        try:
            tipo = normalize_tipo(request.tipo)
            formato = normalize_formato(request.formato)

            if tipo == 'calificaciones':
                dto = self._report_data.fetch_calificaciones(request.materia_id)
                prefix = 'calificaciones'
                sin_datos = 'No hay datos de calificaciones para esta materia'
            else:
                dto = self._report_data.fetch_asistencias(request.materia_id)
                prefix = 'asistencias'
                sin_datos = 'No hay datos de asistencias para esta materia'

            if not dto.alumnos:
                context.abort(grpc.StatusCode.NOT_FOUND, sin_datos)

            contenido, filename, content_type = build_report_bytes(
                dto, prefix=prefix, formato=formato
            )
            return reportes_pb2.ReportResponse(
                success=True,
                archivo=contenido,
                filename=filename,
                content_type=content_type,
            )
        except grpc.RpcError:
            raise
        except Exception as exc:
            _abort_for_exception(context, exc)

    def GetHistorialDocente(self, request, context):
        if request.docente_id <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, 'docente_id debe ser mayor a 0')

        try:
            periodos = self._estadisticas.historial_docente(request.docente_id)
            max_materias = int(config('ESTADISTICAS_DOCENTE_MAX_MATERIAS', default=50))
            if len(periodos) > max_materias:
                periodos = periodos[:max_materias]

            return reportes_pb2.HistorialDocenteResponse(
                docente_id=request.docente_id,
                periodos=[_stats_periodo_proto(p) for p in periodos],
            )
        except grpc.RpcError:
            raise
        except Exception as exc:
            _abort_for_exception(context, exc)


def _stats_periodo_proto(dto: StatsPeriodoDTO) -> reportes_pb2.StatsPeriodo:
    return reportes_pb2.StatsPeriodo(
        periodo_nombre=dto.periodo_nombre,
        periodo_id=dto.periodo_id,
        materia_nombre=dto.materia_nombre,
        materia_id=dto.materia_id,
        total_alumnos=dto.total_alumnos,
        aprobados=dto.aprobados,
        reprobados=dto.reprobados,
        promedio_grupal=dto.promedio_grupal,
        porcentaje_asistencia=dto.porcentaje_asistencia,
    )


def _abort_for_exception(context, exc: Exception) -> None:
    if isinstance(exc, ValueError):
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
    if isinstance(exc, MateriaNotFound):
        context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
    if isinstance(exc, AlumnoNotFound):
        context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
    if isinstance(exc, PermissionDenied):
        context.abort(grpc.StatusCode.PERMISSION_DENIED, str(exc))
    if isinstance(exc, UpstreamUnavailable):
        context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))
    if isinstance(exc, UpstreamGrpcError):
        context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))
    if isinstance(exc, ReportesDomainError):
        context.abort(grpc.StatusCode.INTERNAL, str(exc))
    logger.exception('Error inesperado en RPC reportes')
    context.abort(grpc.StatusCode.INTERNAL, str(exc))
