"""Acceso a read models locales (sin gRPC MS-2/MS-3)."""

from __future__ import annotations

from dataclasses import dataclass

from apps.core.models import AlumnoMateriaProjection, MateriaProjection


@dataclass(frozen=True)
class MateriaLocal:
    materia_id: int
    periodo_id: int
    nrc: str
    nombre: str
    docente_id: int | None
    docente_nombre: str
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
        seccion=row.seccion,
        periodo_nombre=row.periodo_nombre,
    )


def is_alumno_en_materia_local(alumno_id: int, materia_id: int) -> bool:
    return AlumnoMateriaProjection.objects.filter(
        alumno_id=alumno_id,
        materia_id=materia_id,
        activa=True,
    ).exists()


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
