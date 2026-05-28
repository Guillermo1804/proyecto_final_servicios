"""Acceso a read models locales (sin gRPC MS-2/MS-3)."""

from __future__ import annotations

from dataclasses import dataclass

from apps.core.docente_auth import usuario_puede_gestionar_materia as _usuario_puede_gestionar_materia
from apps.core.models import AlumnoMateriaProjection, MateriaProjection


@dataclass(frozen=True)
class MateriaLocal:
    materia_id: int
    periodo_id: int
    nrc: str
    nombre: str
    docente_id: int | None
    docente_nombre: str
    docente_email: str
    seccion: str
    periodo_nombre: str


@dataclass(frozen=True)
class AlumnoLocal:
    id: int
    matricula: str
    nombre: str
    email: str


def get_materia_local(materia_id: int) -> MateriaLocal:
    row = MateriaProjection.objects.filter(materia_id=materia_id).first()
    if row is None:
        raise LookupError(f'Materia {materia_id} no encontrada en proyección local')
    return MateriaLocal(
        materia_id=row.materia_id,
        periodo_id=row.periodo_id,
        nrc=row.nrc,
        nombre=row.nombre,
        docente_id=row.docente_id,
        docente_nombre=row.docente_nombre,
        docente_email=row.docente_email or '',
        seccion=row.seccion,
        periodo_nombre=row.periodo_nombre,
    )


def is_alumno_en_materia_local(alumno_id: int, materia_id: int) -> bool:
    return AlumnoMateriaProjection.objects.filter(
        alumno_id=alumno_id,
        materia_id=materia_id,
        activa=True,
    ).exists()


def ensure_alumno_en_materia_projection(
    materia_id: int,
    alumno_id: int,
    *,
    matricula: str = '',
    nombre: str = '',
    email: str = '',
) -> bool:
    """Valida inscripción local; si falta en proyección, la crea (desfase event bus / MS-3)."""
    if is_alumno_en_materia_local(alumno_id, materia_id):
        return True

    mat = (matricula or '').strip()
    if mat:
        por_matricula = AlumnoMateriaProjection.objects.filter(
            materia_id=materia_id,
            matricula=mat,
            activa=True,
        ).first()
        if por_matricula is not None:
            return por_matricula.alumno_id == alumno_id

    AlumnoMateriaProjection.objects.update_or_create(
        alumno_id=alumno_id,
        materia_id=materia_id,
        defaults={
            'matricula': mat or str(alumno_id),
            'nombre': (nombre or '').strip(),
            'email': (email or '').strip(),
            'activa': True,
        },
    )
    return True


def alumno_puede_ver_materia(materia_id: int, *, usuario_email: str) -> bool:
    email = (usuario_email or '').strip()
    if not email:
        return False
    return AlumnoMateriaProjection.objects.filter(
        materia_id=materia_id,
        activa=True,
        email__iexact=email,
    ).exists()


def usuario_puede_gestionar_materia(
    *,
    usuario_id: int,
    usuario_email: str,
    usuario_rol: str,
    materia: MateriaLocal,
) -> bool:
    return _usuario_puede_gestionar_materia(
        usuario_id=usuario_id,
        usuario_email=usuario_email,
        usuario_rol=usuario_rol,
        docente_id_materia=getattr(materia, 'docente_id', None),
        docente_nombre_materia=getattr(materia, 'docente_nombre', '') or '',
        docente_email_materia=getattr(materia, 'docente_email', '') or '',
    )


def list_alumnos_materia_local(materia_id: int) -> list[AlumnoLocal]:
    rows = AlumnoMateriaProjection.objects.filter(
        materia_id=materia_id,
        activa=True,
    ).order_by('alumno_id')
    return [
        AlumnoLocal(
            id=row.alumno_id,
            matricula=row.matricula,
            nombre=row.nombre,
            email=row.email,
        )
        for row in rows
    ]
