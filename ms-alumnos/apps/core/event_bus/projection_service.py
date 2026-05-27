"""Proyecciones locales MS-3 desde eventos de dominio."""

from __future__ import annotations

from typing import Any

from apps.core.models import MateriaProjection


def upsert_materia(payload: dict[str, Any], **extra: Any) -> MateriaProjection:
    defaults = {
        "periodo_id": int(payload.get("periodo_id") or 0),
        "nrc": payload.get("nrc", "") or "",
        "nombre": payload.get("nombre", "") or "",
        "seccion": payload.get("seccion", "") or "",
        "clave": payload.get("clave", "") or "",
        "horario": payload.get("horario", "") or "",
        "docente_nombre": payload.get("docente_nombre", "") or "",
        "docente_id": payload.get("docente_id"),
        "periodo_nombre": payload.get("periodo_nombre", "") or "",
        **extra,
    }
    row, _ = MateriaProjection.objects.update_or_create(
        materia_id=int(payload["materia_id"]),
        defaults=defaults,
    )
    return row


def assign_teacher(payload: dict[str, Any]) -> None:
    materia_id = int(payload["materia_id"])
    updates = {
        "docente_nombre": payload.get("docente_nombre", "") or "",
        "docente_id": payload.get("docente_id"),
        "periodo_id": int(payload.get("periodo_id") or 0),
    }
    if payload.get("nrc"):
        updates["nrc"] = payload["nrc"]
    if MateriaProjection.objects.filter(materia_id=materia_id).exists():
        MateriaProjection.objects.filter(materia_id=materia_id).update(**updates)
    else:
        upsert_materia(
            {
                "materia_id": materia_id,
                "periodo_id": payload.get("periodo_id", 0),
                "nrc": payload.get("nrc", ""),
                "nombre": payload.get("nombre", "") or f"Materia {materia_id}",
            },
            docente_nombre=updates["docente_nombre"],
            docente_id=updates["docente_id"],
        )
