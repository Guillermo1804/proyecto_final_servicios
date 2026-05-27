"""Actualización incremental de proyecciones analíticas MS-7."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db.models import Avg

from apps.reportes.models import (
    ReporteAlumnoProjection,
    ReporteAsistenciaProjection,
    ReporteCalificacionProjection,
    ReporteMateriaProjection,
    ReportePeriodoProjection,
)
from apps.reportes.services.analytics_state import touch_data_as_of


def _decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    if value is None:
        return default
    return Decimal(str(value))


def _periodo_nombre(periodo_id: int) -> str:
    row = ReportePeriodoProjection.objects.filter(periodo_id=periodo_id).first()
    return row.nombre if row else ''


def upsert_periodo(payload: dict[str, Any], *, activo: bool | None = None) -> None:
    periodo_id = payload['periodo_id']
    defaults = {
        'nombre': payload.get('nombre', ''),
        'activo': activo if activo is not None else bool(payload.get('activo', True)),
    }
    ReportePeriodoProjection.objects.update_or_create(periodo_id=periodo_id, defaults=defaults)
    ReporteMateriaProjection.objects.filter(periodo_id=periodo_id).update(
        periodo_nombre=defaults['nombre'],
    )
    touch_data_as_of()


def upsert_materia(payload: dict[str, Any], **extra: Any) -> None:
    periodo_id = payload.get('periodo_id', 0)
    ReporteMateriaProjection.objects.update_or_create(
        materia_id=payload['materia_id'],
        defaults={
            'periodo_id': periodo_id,
            'periodo_nombre': payload.get('periodo_nombre') or _periodo_nombre(periodo_id),
            'nrc': payload.get('nrc', ''),
            'nombre': payload.get('nombre', ''),
            'seccion': payload.get('seccion', ''),
            'clave': payload.get('clave', ''),
            'docente_id': payload.get('docente_id'),
            'docente_nombre': payload.get('docente_nombre', ''),
            'horario': payload.get('horario', ''),
            **extra,
        },
    )
    touch_data_as_of()


def mark_materia_closed(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    if ReporteMateriaProjection.objects.filter(materia_id=materia_id).exists():
        ReporteMateriaProjection.objects.filter(materia_id=materia_id).update(
            cerrada=True,
            nrc=payload.get('nrc', '') or '',
            nombre=payload.get('nombre', '') or '',
        )
    else:
        upsert_materia(payload, cerrada=True)
    touch_data_as_of()


def mark_calificaciones_cerradas(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    ReporteMateriaProjection.objects.filter(materia_id=materia_id).update(cerrada=True)
    touch_data_as_of()


def upsert_alumno_materia(
    *,
    alumno_id: int,
    materia_id: int,
    matricula: str,
    nombre: str,
    email: str,
    usuario_id: int | None = None,
    activa: bool = True,
) -> None:
    defaults = {
        'matricula': matricula,
        'nombre': nombre,
        'email': email or '',
        'activa': activa,
    }
    if usuario_id is not None:
        defaults['usuario_id'] = usuario_id
    ReporteAlumnoProjection.objects.update_or_create(
        alumno_id=alumno_id,
        materia_id=materia_id,
        defaults=defaults,
    )
    _refresh_materia_enrollment_count(materia_id)
    touch_data_as_of()


def handle_alumno_imported(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    if not ReporteMateriaProjection.objects.filter(materia_id=materia_id).exists():
        upsert_materia(
            {
                'materia_id': materia_id,
                'periodo_id': payload.get('periodo_id', 0),
                'nrc': payload.get('nrc', ''),
                'nombre': payload.get('materia_nombre', f'Materia {materia_id}'),
                'docente_nombre': payload.get('docente_nombre', ''),
            }
        )
    upsert_alumno_materia(
        alumno_id=payload['alumno_id'],
        materia_id=materia_id,
        matricula=payload.get('matricula', ''),
        nombre=payload.get('nombre', ''),
        email=payload.get('email', ''),
        activa=True,
    )


def handle_alumno_updated(payload: dict[str, Any]) -> None:
    alumno_id = payload['alumno_id']
    updates: dict[str, Any] = {}
    if payload.get('nombre'):
        updates['nombre'] = payload['nombre']
    if payload.get('email'):
        updates['email'] = payload['email']
    if payload.get('matricula'):
        updates['matricula'] = payload['matricula']
    if 'activo' in payload:
        updates['activa'] = bool(payload['activo'])
    if payload.get('usuario_id') is not None:
        updates['usuario_id'] = payload['usuario_id']
    if updates:
        ReporteAlumnoProjection.objects.filter(alumno_id=alumno_id).update(**updates)
    if payload.get('materia_id'):
        handle_alumno_imported(payload)
    touch_data_as_of()


def handle_alumno_withdrawn(payload: dict[str, Any]) -> None:
    ReporteAlumnoProjection.objects.filter(
        alumno_id=payload['alumno_id'],
        materia_id=payload['materia_id'],
    ).update(activa=False)
    _refresh_materia_enrollment_count(payload['materia_id'])
    touch_data_as_of()


def handle_actividad_created(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    if not ReporteMateriaProjection.objects.filter(materia_id=materia_id).exists():
        upsert_materia({'materia_id': materia_id, 'periodo_id': 0, 'nrc': '', 'nombre': ''})
    for row in ReporteAlumnoProjection.objects.filter(materia_id=materia_id, activa=True):
        ReporteCalificacionProjection.objects.update_or_create(
            actividad_id=payload['actividad_id'],
            alumno_id=row.alumno_id,
            defaults={
                'materia_id': materia_id,
                'categoria': payload.get('categoria', ''),
                'actividad_nombre': payload.get('nombre', ''),
            },
        )
    touch_data_as_of()


def handle_calificacion_updated(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    cal = _decimal(payload['calificacion'])
    ReporteCalificacionProjection.objects.update_or_create(
        actividad_id=payload['actividad_id'],
        alumno_id=payload['alumno_id'],
        defaults={
            'materia_id': materia_id,
            'calificacion_id': payload.get('calificacion_id'),
            'calificacion': cal,
        },
    )
    _recalc_alumno_promedio(payload['alumno_id'], materia_id)
    touch_data_as_of()


def handle_concentrado_calculado(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    updates = {
        'total_alumnos': int(payload.get('total_alumnos', 0)),
        'promedio_grupal': _decimal(payload.get('promedio_grupal', 0)),
    }
    if payload.get('nrc'):
        updates['nrc'] = payload['nrc']
    if payload.get('materia_nombre'):
        updates['nombre'] = payload['materia_nombre']
    ReporteMateriaProjection.objects.filter(materia_id=materia_id).update(**updates)
    _recalc_aprobados_reprobados(materia_id)
    touch_data_as_of()


def handle_qr_session_created(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    mat, _ = ReporteMateriaProjection.objects.get_or_create(
        materia_id=materia_id,
        defaults={'periodo_id': 0, 'nrc': '', 'nombre': ''},
    )
    mat.total_sesiones_qr += 1
    mat.save(update_fields=['total_sesiones_qr', 'updated_at'])
    _recalc_ausentes_materia(materia_id)
    _recalc_porcentaje_grupal(materia_id)
    touch_data_as_of()


def handle_asistencia_registered(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    alumno_id = payload['alumno_id']
    sesion_id = payload['sesion_id']
    estado = payload['estado']

    ReporteAsistenciaProjection.objects.update_or_create(
        sesion_id=sesion_id,
        alumno_id=alumno_id,
        defaults={
            'materia_id': materia_id,
            'estado': estado,
            'minuto_registro': int(payload.get('minuto_registro', 0)),
            'registro_id': payload.get('registro_id'),
        },
    )

    alumno, _ = ReporteAlumnoProjection.objects.get_or_create(
        alumno_id=alumno_id,
        materia_id=materia_id,
        defaults={'matricula': '', 'nombre': '', 'email': ''},
    )
    if estado == 'presente':
        alumno.presentes += 1
    elif estado == 'retardo':
        alumno.retardos += 1
    alumno.save(update_fields=['presentes', 'retardos', 'updated_at'])

    mat = ReporteMateriaProjection.objects.filter(materia_id=materia_id).first()
    total_sesiones = mat.total_sesiones_qr if mat else 0
    if total_sesiones > 0:
        asistidos = alumno.presentes + alumno.retardos
        alumno.porcentaje_asistencia = _decimal(asistidos * 100 / total_sesiones)
        alumno.ausentes = max(0, total_sesiones - asistidos)
        alumno.save(update_fields=['porcentaje_asistencia', 'ausentes', 'updated_at'])

    _recalc_porcentaje_grupal(materia_id)
    touch_data_as_of()


def handle_asistencia_rejected(payload: dict[str, Any]) -> None:
    touch_data_as_of()


def _recalc_alumno_promedio(alumno_id: int, materia_id: int) -> None:
    agg = (
        ReporteCalificacionProjection.objects.filter(
            alumno_id=alumno_id,
            materia_id=materia_id,
            calificacion__isnull=False,
        ).aggregate(avg=Avg('calificacion'))
    )
    avg = agg['avg']
    if avg is None:
        return
    promedio_real = _decimal(avg)
    ReporteAlumnoProjection.objects.filter(
        alumno_id=alumno_id,
        materia_id=materia_id,
    ).update(
        promedio_real=promedio_real,
        promedio_redondeado=int(round(float(promedio_real))),
    )
    _recalc_aprobados_reprobados(materia_id)


def _recalc_aprobados_reprobados(materia_id: int) -> None:
    qs = ReporteAlumnoProjection.objects.filter(materia_id=materia_id, activa=True)
    aprobados = qs.filter(promedio_redondeado__gte=6).count()
    reprobados = qs.filter(promedio_redondeado__lt=6, promedio_redondeado__gt=0).count()
    ReporteMateriaProjection.objects.filter(materia_id=materia_id).update(
        aprobados=aprobados,
        reprobados=reprobados,
    )


def _refresh_materia_enrollment_count(materia_id: int) -> None:
    total = ReporteAlumnoProjection.objects.filter(materia_id=materia_id, activa=True).count()
    ReporteMateriaProjection.objects.filter(materia_id=materia_id).update(total_alumnos=total)


def _recalc_ausentes_materia(materia_id: int) -> None:
    mat = ReporteMateriaProjection.objects.filter(materia_id=materia_id).first()
    if not mat or mat.total_sesiones_qr <= 0:
        return
    for alumno in ReporteAlumnoProjection.objects.filter(materia_id=materia_id, activa=True):
        asistidos = alumno.presentes + alumno.retardos
        alumno.ausentes = max(0, mat.total_sesiones_qr - asistidos)
        if mat.total_sesiones_qr:
            alumno.porcentaje_asistencia = _decimal(asistidos * 100 / mat.total_sesiones_qr)
        alumno.save(update_fields=['ausentes', 'porcentaje_asistencia', 'updated_at'])


def _recalc_porcentaje_grupal(materia_id: int) -> None:
    agg = ReporteAlumnoProjection.objects.filter(
        materia_id=materia_id,
        activa=True,
    ).aggregate(avg_pct=Avg('porcentaje_asistencia'))
    avg_pct = agg['avg_pct']
    if avg_pct is not None:
        ReporteMateriaProjection.objects.filter(materia_id=materia_id).update(
            porcentaje_asistencia_grupal=_decimal(avg_pct),
        )
