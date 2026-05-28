"""Actualización de read models MS-5 desde eventos upstream."""

from __future__ import annotations

from typing import Any

from apps.core.models import AlumnoProjection, MateriaProjection, PeriodoProjection


def upsert_periodo(payload: dict[str, Any], *, activo: bool | None = None) -> None:
    periodo_id = payload['periodo_id']
    defaults = {
        'nombre': payload.get('nombre', ''),
        'activo': activo if activo is not None else bool(payload.get('activo', True)),
    }
    PeriodoProjection.objects.update_or_create(periodo_id=periodo_id, defaults=defaults)
    MateriaProjection.objects.filter(periodo_id=periodo_id).update(
        periodo_activo=defaults['activo'],
    )


def upsert_materia(payload: dict[str, Any], **extra: Any) -> None:
    periodo_id = payload.get('periodo_id', 0)
    periodo_activo = True
    periodo = PeriodoProjection.objects.filter(periodo_id=periodo_id).first()
    if periodo is not None:
        periodo_activo = periodo.activo
    MateriaProjection.objects.update_or_create(
        materia_id=payload['materia_id'],
        defaults={
            'periodo_id': periodo_id,
            'nrc': payload.get('nrc', ''),
            'nombre': payload.get('nombre', ''),
            'docente_id': payload.get('docente_id'),
            'periodo_activo': periodo_activo,
            **extra,
        },
    )


def mark_materia_closed(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    if MateriaProjection.objects.filter(materia_id=materia_id).exists():
        MateriaProjection.objects.filter(materia_id=materia_id).update(
            cerrada_upstream=True,
            nrc=payload.get('nrc', '') or '',
            nombre=payload.get('nombre', '') or '',
        )
    else:
        upsert_materia(payload, cerrada_upstream=True)


def upsert_alumno_materia(
    *,
    alumno_id: int,
    materia_id: int,
    matricula: str,
    nombre: str,
    email: str,
    activa: bool = True,
) -> None:
    AlumnoProjection.objects.update_or_create(
        alumno_id=alumno_id,
        materia_id=materia_id,
        defaults={
            'matricula': matricula,
            'nombre': nombre,
            'email': email or '',
            'activa': activa,
        },
    )


def handle_alumno_imported(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    if not MateriaProjection.objects.filter(materia_id=materia_id).exists():
        upsert_materia(
            {
                'materia_id': materia_id,
                'periodo_id': payload.get('periodo_id', 0),
                'nrc': payload.get('nrc', ''),
                'nombre': payload.get('materia_nombre', f'Materia {materia_id}'),
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
    alumno_id = payload.get('alumno_id')
    if alumno_id is None:
        return
    updates = {}
    if payload.get('nombre'):
        updates['nombre'] = payload['nombre']
    if payload.get('email'):
        updates['email'] = payload['email']
    if payload.get('matricula'):
        updates['matricula'] = payload['matricula']
    if updates:
        AlumnoProjection.objects.filter(alumno_id=alumno_id).update(**updates)
    if payload.get('materia_id'):
        handle_alumno_imported(payload)


def handle_alumno_withdrawn(payload: dict[str, Any]) -> None:
    AlumnoProjection.objects.filter(
        alumno_id=payload['alumno_id'],
        materia_id=payload['materia_id'],
    ).update(activa=False)
