"""Actualización de read models desde payloads de eventos."""

from __future__ import annotations

from typing import Any

from apps.core.models import AlumnoMateriaProjection, DocenteProjection, MateriaProjection, UserProjection


def _link_docente_usuario_by_email(*, usuario_id: int, email: str) -> None:
    normalized = (email or '').strip().lower()
    if not normalized:
        return
    DocenteProjection.objects.filter(email__iexact=normalized).update(usuario_id=usuario_id)


def upsert_user(payload: dict[str, Any]) -> None:
    UserProjection.objects.update_or_create(
        user_id=payload['user_id'],
        defaults={
            'email': payload.get('email', ''),
            'nombre': payload.get('nombre', ''),
            'rol': payload.get('rol', ''),
            'activo': bool(payload.get('activo', True)),
        },
    )
    if (payload.get('rol') or '').lower() == 'docente':
        _link_docente_usuario_by_email(
            usuario_id=int(payload['user_id']),
            email=str(payload.get('email', '')),
        )


def upsert_docente(payload: dict[str, Any]) -> None:
    docente_id = payload.get('docente_id')
    if docente_id is None:
        return
    nombre = f"{payload.get('nombre', '')} {payload.get('apellido', '')}".strip()
    DocenteProjection.objects.update_or_create(
        docente_id=int(docente_id),
        defaults={
            'email': payload.get('email', '') or '',
            'nombre': nombre,
        },
    )


def apply_periodo(payload: dict[str, Any], *, activo: bool | None = None) -> None:
    periodo_id = payload['periodo_id']
    nombre = payload.get('nombre', '')
    periodo_activo = activo if activo is not None else bool(payload.get('activo', True))
    MateriaProjection.objects.filter(periodo_id=periodo_id).update(
        periodo_nombre=nombre,
        periodo_activo=periodo_activo,
    )


def upsert_materia(payload: dict[str, Any], **extra: Any) -> MateriaProjection:
    defaults = {
        'periodo_id': payload.get('periodo_id', 0),
        'nrc': payload.get('nrc', ''),
        'nombre': payload.get('nombre', ''),
        'seccion': payload.get('seccion', ''),
        'clave': payload.get('clave', ''),
        'horario': payload.get('horario', ''),
        'docente_nombre': payload.get('docente_nombre', ''),
        'docente_id': payload.get('docente_id'),
        **extra,
    }
    row, _ = MateriaProjection.objects.update_or_create(
        materia_id=payload['materia_id'],
        defaults=defaults,
    )
    return row


def assign_teacher(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    updates = {
        'docente_nombre': payload.get('docente_nombre', ''),
        'docente_id': payload.get('docente_id'),
        'periodo_id': payload.get('periodo_id', 0),
    }
    if payload.get('nrc'):
        updates['nrc'] = payload['nrc']
    MateriaProjection.objects.filter(materia_id=materia_id).update(**updates)
    if not MateriaProjection.objects.filter(materia_id=materia_id).exists():
        upsert_materia(
            {
                'materia_id': materia_id,
                'periodo_id': payload.get('periodo_id', 0),
                'nrc': payload.get('nrc', ''),
                'nombre': f'Materia {materia_id}',
            },
            docente_nombre=updates['docente_nombre'],
            docente_id=updates['docente_id'],
        )


def mark_materia_closed_upstream(payload: dict[str, Any]) -> None:
    materia_id = payload['materia_id']
    if MateriaProjection.objects.filter(materia_id=materia_id).exists():
        MateriaProjection.objects.filter(materia_id=materia_id).update(
            materia_cerrada_upstream=True,
            nrc=payload.get('nrc', '') or '',
            nombre=payload.get('nombre', '') or '',
        )
    else:
        upsert_materia(payload, materia_cerrada_upstream=True)


def upsert_alumno_materia(
    *,
    alumno_id: int,
    materia_id: int,
    matricula: str,
    nombre: str,
    email: str,
    activa: bool = True,
) -> None:
    AlumnoMateriaProjection.objects.update_or_create(
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
            },
            docente_email=payload.get('docente_email', ''),
            docente_nombre=payload.get('docente_nombre', ''),
        )
    else:
        MateriaProjection.objects.filter(materia_id=materia_id).update(
            docente_email=payload.get('docente_email', '') or '',
            docente_nombre=payload.get('docente_nombre', '') or '',
            nombre=payload.get('materia_nombre', '') or '',
            nrc=payload.get('nrc', '') or '',
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
        AlumnoMateriaProjection.objects.filter(alumno_id=alumno_id).update(**updates)
    materia_id = payload.get('materia_id')
    if materia_id:
        handle_alumno_imported(payload)


def handle_alumno_withdrawn(payload: dict[str, Any]) -> None:
    AlumnoMateriaProjection.objects.filter(
        alumno_id=payload['alumno_id'],
        materia_id=payload['materia_id'],
    ).update(activa=False)
