"""Payloads de eventos de dominio MS-2."""

from __future__ import annotations

from apps.core.models import Materia, Periodo


def periodo_payload(periodo: Periodo) -> dict:
    return {
        "periodo_id": periodo.id,
        "nombre": periodo.nombre,
        "fecha_inicio": periodo.fecha_inicio.isoformat(),
        "fecha_fin": periodo.fecha_fin.isoformat(),
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
