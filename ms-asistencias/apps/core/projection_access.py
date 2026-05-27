"""Validaciones de negocio contra proyecciones locales (sin gRPC MS-3)."""

from __future__ import annotations

from dataclasses import dataclass

from apps.core.models import AlumnoProjection, MateriaProjection, PeriodoProjection


@dataclass(frozen=True)
class MateriaLocal:
    materia_id: int
    periodo_id: int
    nrc: str
    nombre: str
    cerrada_upstream: bool
    periodo_activo: bool


class ProjectionRejection(Exception):
    def __init__(self, message: str, *, codigo: str) -> None:
        super().__init__(message)
        self.codigo = codigo


def get_materia_local(materia_id: int) -> MateriaLocal:
    row = MateriaProjection.objects.filter(materia_id=materia_id).first()
    if row is None:
        return MateriaLocal(
            materia_id=materia_id,
            periodo_id=0,
            nrc='',
            nombre='',
            cerrada_upstream=False,
            periodo_activo=True,
        )
    periodo_activo = row.periodo_activo
    periodo = PeriodoProjection.objects.filter(periodo_id=row.periodo_id).first()
    if periodo is not None:
        periodo_activo = periodo.activo
    return MateriaLocal(
        materia_id=row.materia_id,
        periodo_id=row.periodo_id,
        nrc=row.nrc,
        nombre=row.nombre,
        cerrada_upstream=row.cerrada_upstream,
        periodo_activo=periodo_activo,
    )


def assert_materia_habilitada_para_asistencia(materia_id: int) -> MateriaLocal:
    materia = get_materia_local(materia_id)
    if materia.cerrada_upstream:
        raise ProjectionRejection(
            f'La materia {materia_id} está cerrada upstream',
            codigo='materia_cerrada',
        )
    if not materia.periodo_activo:
        raise ProjectionRejection(
            f'El periodo de la materia {materia_id} no está activo',
            codigo='periodo_inactivo',
        )
    return materia


def is_alumno_en_materia_local(alumno_id: int, materia_id: int) -> bool:
    return AlumnoProjection.objects.filter(
        alumno_id=alumno_id,
        materia_id=materia_id,
        activa=True,
    ).exists()


def assert_alumno_inscrito(alumno_id: int, materia_id: int) -> AlumnoProjection:
    row = AlumnoProjection.objects.filter(
        alumno_id=alumno_id,
        materia_id=materia_id,
    ).first()
    if row is None or not row.activa:
        raise ProjectionRejection(
            f'El alumno {alumno_id} no está inscrito activo en materia {materia_id}',
            codigo='alumno_no_inscrito',
        )
    return row
