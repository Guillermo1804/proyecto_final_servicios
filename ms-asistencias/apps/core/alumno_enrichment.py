"""Enriquecimiento de registros de asistencia con datos de MS-3 (gRPC)."""

from __future__ import annotations

import logging
from typing import Any

from grpc_clients import get_alumno_by_id

logger = logging.getLogger(__name__)

_alumno_cache: dict[int, dict[str, str]] = {}


def _lookup_alumno(alumno_id: int) -> dict[str, str]:
    if alumno_id in _alumno_cache:
        return _alumno_cache[alumno_id]
    try:
        info = get_alumno_by_id(alumno_id)
        payload = {
            'alumno_nombre': (info.nombre or '').strip(),
            'matricula': (info.matricula or '').strip(),
        }
    except Exception as exc:
        logger.warning('MS-3 GetAlumnoById(%s) falló: %s', alumno_id, exc)
        payload = {'alumno_nombre': '', 'matricula': ''}
    _alumno_cache[alumno_id] = payload
    return payload


def enrich_registros(registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Añade alumno_nombre y matricula a cada registro serializado."""
    enriched: list[dict[str, Any]] = []
    for row in registros:
        item = dict(row)
        alumno_id = item.get('alumno_id')
        if alumno_id:
            item.update(_lookup_alumno(int(alumno_id)))
        else:
            item.setdefault('alumno_nombre', '')
            item.setdefault('matricula', '')
        enriched.append(item)
    return enriched


def clear_alumno_cache() -> None:
    """Útil en tests."""
    _alumno_cache.clear()
