"""Endpoints REST de estadísticas JSON (ISSUE-905, 906)."""

from collections import defaultdict

from decouple import config
from rest_framework.decorators import api_view

from apps.reportes.dto.report_dto import AlumnoStatsDTO, StatsPeriodoDTO
from apps.reportes.services.estadisticas_service import EstadisticasService
from apps.reportes.views.reportes_views import _authenticate
from grpc_clients import alumnos_client
from grpc_clients.exceptions import AlumnoNotFound, ReportesDomainError, UpstreamUnavailable
from utils.responses import error_response, success_response

DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 100


def _stats_periodo_dict(dto: StatsPeriodoDTO) -> dict:
    return {
        'periodo_nombre': dto.periodo_nombre,
        'periodo_id': dto.periodo_id,
        'materia_nombre': dto.materia_nombre,
        'materia_id': dto.materia_id,
        'total_alumnos': dto.total_alumnos,
        'aprobados': dto.aprobados,
        'reprobados': dto.reprobados,
        'promedio_grupal': dto.promedio_grupal,
        'porcentaje_asistencia': dto.porcentaje_asistencia,
    }


def _materia_alumno_dict(dto) -> dict:
    return {
        'materia_id': dto.materia_id,
        'materia_nombre': dto.materia_nombre,
        'periodo_nombre': dto.periodo_nombre,
        'promedio_real': dto.promedio_real,
        'promedio_redondeado': dto.promedio_redondeado,
        'total_sesiones': dto.total_sesiones,
        'presentes': dto.presentes,
        'retardos': dto.retardos,
        'ausentes': dto.ausentes,
        'porcentaje_asistencia': dto.porcentaje_asistencia,
    }


def _alumno_stats_dict(dto: AlumnoStatsDTO) -> dict:
    return {
        'alumno_id': dto.alumno_id,
        'matricula': dto.matricula,
        'nombre': dto.nombre,
        'email': dto.email,
        'materias': [_materia_alumno_dict(m) for m in dto.materias],
    }


def _build_comparativa(periodos: tuple[StatsPeriodoDTO, ...]) -> list[dict]:
    """Agrupa historial por nombre de materia (comparativa multi-periodo)."""
    grupos: dict[str, list[dict]] = defaultdict(list)
    for item in periodos:
        grupos[item.materia_nombre].append(_stats_periodo_dict(item))
    return [
        {'materia_nombre': nombre, 'periodos': registros}
        for nombre, registros in sorted(grupos.items())
    ]


def _paginate(items: tuple, request) -> tuple[list, dict | None]:
    if not request.query_params.get('page') and not request.query_params.get('limit'):
        return list(items), None

    page = max(1, int(request.query_params.get('page', 1)))
    limit = min(
        max(1, int(request.query_params.get('limit', DEFAULT_PAGE_LIMIT))),
        MAX_PAGE_LIMIT,
    )
    total = len(items)
    start = (page - 1) * limit
    end = start + limit
    return list(items[start:end]), {
        'page': page,
        'limit': limit,
        'total': total,
        'count': max(0, min(limit, total - start)),
    }


def _check_docente_access(request, usuario_id: int):
    if request.user_rol == 'admin':
        return None
    if request.user_rol != 'docente':
        return error_response('Sin permisos para consultar estadísticas de docente', status=403)
    if usuario_id != request.user_id:
        return error_response('Solo puede consultar sus propias estadísticas', status=403)
    return None


def _check_alumno_access(request, alumno_id: int):
    if request.user_rol == 'admin':
        return None
    if request.user_rol != 'alumno':
        return error_response('Sin permisos para consultar estadísticas de alumno', status=403)
    try:
        alumno = alumnos_client.get_alumno_by_id(alumno_id)
    except AlumnoNotFound:
        return error_response('Alumno no encontrado', status=404)
    except UpstreamUnavailable as exc:
        return error_response(str(exc), status=503)
    if alumno.usuario_id != request.user_id:
        return error_response('Solo puede consultar sus propias estadísticas', status=403)
    return None


@api_view(['GET'])
def estadisticas_docente(request, usuario_id: int):
    """GET /estadisticas/docente/<usuario_id> — resumen multi-periodo (ISSUE-905)."""
    _, err = _authenticate(request)
    if err:
        return err

    denied = _check_docente_access(request, usuario_id)
    if denied:
        return denied

    try:
        periodos = EstadisticasService().historial_docente(usuario_id)
    except UpstreamUnavailable as exc:
        return error_response(str(exc), status=503)
    except ReportesDomainError as exc:
        return error_response(str(exc), status=500)

    max_materias = int(config('ESTADISTICAS_DOCENTE_MAX_MATERIAS', default=50))
    if len(periodos) > max_materias:
        periodos = periodos[:max_materias]

    paginados, pagination = _paginate(periodos, request)

    data = {
        'docente_id': usuario_id,
        'periodos': [_stats_periodo_dict(p) for p in paginados],
        'comparativa': _build_comparativa(periodos),
    }
    return success_response(data, pagination=pagination)


@api_view(['GET'])
def estadisticas_alumno(request, alumno_id: int):
    """GET /estadisticas/alumno/<alumno_id> — historial académico y asistencia (ISSUE-906)."""
    _, err = _authenticate(request)
    if err:
        return err

    denied = _check_alumno_access(request, alumno_id)
    if denied:
        return denied

    try:
        stats = EstadisticasService().stats_alumno(alumno_id)
    except AlumnoNotFound:
        return error_response('Alumno no encontrado', status=404)
    except UpstreamUnavailable as exc:
        return error_response(str(exc), status=503)
    except ReportesDomainError as exc:
        return error_response(str(exc), status=500)

    materias, pagination = _paginate(stats.materias, request)
    payload = _alumno_stats_dict(stats)
    payload['materias'] = [_materia_alumno_dict(m) for m in materias]

    return success_response(payload, pagination=pagination)
