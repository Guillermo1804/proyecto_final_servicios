"""Payloads de eventos de dominio MS-2."""

from __future__ import annotations

from apps.core.models import Materia, Periodo


def _iso_date(value) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def periodo_payload(periodo: Periodo) -> dict:
    return {
        "periodo_id": periodo.id,
        "nombre": periodo.nombre,
        "fecha_inicio": _iso_date(periodo.fecha_inicio),
        "fecha_fin": _iso_date(periodo.fecha_fin),
        "plan_estudios": periodo.plan_estudios,
        "activo": periodo.activo,
    }


def materia_payload(materia: Materia) -> dict:
    return {
        "materia_id": materia.id,
        "periodo_id": materia.periodo_id,
        "nrc": materia.nrc,
        "nombre": materia.nombre,
        "seccion": materia.seccion,
        "clave": materia.clave,
        "docente_nombre": materia.docente_nombre,
        "docente_id": materia.docente_id,
        "horario": materia.horario,
    }
