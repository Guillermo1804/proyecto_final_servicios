"""Endpoints REST de descarga de reportes (ISSUE-902, 903, 904)."""

from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view

from apps.reportes.dto.report_dto import AsistenciasReportDTO, CalificacionesReportDTO
from apps.reportes.services.report_data_service import ReportDataService
from apps.reportes.services.report_export import build_report_bytes, normalize_formato
from apps.reportes.exceptions import MateriaNotFound, ReportesDomainError
from utils.auth import validate_token
from utils.responses import error_response, format_data_as_of


def _extract_token(request) -> str:
    return (
        request.headers.get('Authorization', '')
        .replace('Bearer ', '')
        .strip()
    )


def _authenticate(request):
    token = _extract_token(request)
    if not token:
        return None, error_response('Token requerido', status=401)
    try:
        auth = validate_token(token)
    except ValueError as exc:
        message = str(exc)
        code = 403 if message == 'Sin permisos' else 401
        return None, error_response(message, status=code)
    request.user_id = auth.user_id
    request.user_rol = auth.rol
    request.user_email = auth.email
    return auth, None


def _check_reporte_access(request, materia_docente_id: int):
    if request.user_rol == 'admin':
        return None
    if request.user_rol != 'docente':
        return error_response('Sin permisos para generar reportes', status=403)
    if materia_docente_id != request.user_id:
        return error_response('No es el docente titular de la materia', status=403)
    return None


def _file_response(
    buffer, filename: str, content_type: str, *, data_as_of=None
) -> FileResponse:
    response = FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type=content_type,
    )
    if data_as_of:
        response['X-AGM-Data-As-Of'] = format_data_as_of(data_as_of)
    return response


def _render_reporte(
    dto: CalificacionesReportDTO | AsistenciasReportDTO,
    *,
    prefix: str,
    formato: str,
):
    contenido, filename, content_type = build_report_bytes(dto, prefix=prefix, formato=formato)
    from io import BytesIO

    return _file_response(
        BytesIO(contenido),
        filename,
        content_type,
        data_as_of=getattr(dto, 'data_as_of', None),
    )


@api_view(['GET'])
def reporte_calificaciones(request, materia_id: int):
    """GET /reportes/calificaciones/<materia_id>?formato=xlsx|xls|pdf"""
    _, err = _authenticate(request)
    if err:
        return err

    try:
        formato = normalize_formato(request.query_params.get('formato'))
    except ValueError as exc:
        return error_response(str(exc), status=400)

    try:
        dto = ReportDataService().fetch_calificaciones(materia_id)
    except MateriaNotFound:
        return error_response('Materia no encontrada', status=404)
    except ReportesDomainError as exc:
        return error_response(str(exc), status=500)

    denied = _check_reporte_access(request, dto.materia.docente_id)
    if denied:
        return denied

    if not dto.alumnos:
        return error_response('No hay datos de calificaciones para esta materia', status=404)

    return _render_reporte(dto, prefix='calificaciones', formato=formato)


@api_view(['GET'])
def reporte_asistencias(request, materia_id: int):
    """GET /reportes/asistencias/<materia_id>?formato=xlsx|xls|pdf"""
    _, err = _authenticate(request)
    if err:
        return err

    try:
        formato = normalize_formato(request.query_params.get('formato'))
    except ValueError as exc:
        return error_response(str(exc), status=400)

    try:
        dto = ReportDataService().fetch_asistencias(materia_id)
    except MateriaNotFound:
        return error_response('Materia no encontrada', status=404)
    except ReportesDomainError as exc:
        return error_response(str(exc), status=500)

    denied = _check_reporte_access(request, dto.materia.docente_id)
    if denied:
        return denied

    if not dto.alumnos:
        return error_response('No hay datos de asistencias para esta materia', status=404)

    return _render_reporte(dto, prefix='asistencias', formato=formato)
