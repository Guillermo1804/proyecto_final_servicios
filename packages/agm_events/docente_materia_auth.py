"""Reglas compartidas: usuario MS-1 vs titularidad de materia (MS-2/MS-3)."""

from __future__ import annotations

import unicodedata
from typing import Protocol


class DocenteRecord(Protocol):
    docente_id: int
    usuario_id: int | None
    email: str
    nombre: str


def normalize_docente_nombre(value: str) -> str:
    normalized = unicodedata.normalize('NFKD', value or '')
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    return ' '.join(ascii_text.lower().replace('-', ' ').split())


def docente_nombres_coinciden(nombre_materia: str, nombre_docente: str) -> bool:
    en_materia = normalize_docente_nombre(nombre_materia)
    if not en_materia:
        return False

    tokens = [
        token
        for token in normalize_docente_nombre(nombre_docente).split()
        if len(token) >= 2
    ]
    if not tokens:
        return False

    coincidencias = sum(1 for token in tokens if token in en_materia)
    minimo = len(tokens) if len(tokens) <= 2 else 2
    return coincidencias >= minimo


def usuario_puede_gestionar_materia_docente(
    *,
    usuario_id: int,
    usuario_email: str,
    usuario_rol: str,
    docente_id_materia: int | None,
    docente_nombre_materia: str,
    docente_email_materia: str,
    docente_titular: DocenteRecord | None,
    docente_usuario: DocenteRecord | None,
) -> bool:
    rol = (usuario_rol or '').lower()
    if rol == 'admin':
        return True
    if rol != 'docente':
        return False

    if docente_id_materia is None and not (docente_nombre_materia or '').strip():
        return False

    if docente_id_materia is not None and usuario_id == docente_id_materia:
        return True

    if docente_titular and docente_titular.usuario_id == usuario_id:
        return True

    if docente_usuario:
        if docente_id_materia is not None and docente_usuario.docente_id == docente_id_materia:
            return True
        if docente_nombres_coinciden(docente_nombre_materia, docente_usuario.nombre):
            return True

    email = (usuario_email or '').strip().lower()
    if email:
        if docente_titular and (docente_titular.email or '').strip().lower() == email:
            return True
        if docente_usuario and (docente_usuario.email or '').strip().lower() == email:
            return True
        materia_email = (docente_email_materia or '').strip().lower()
        if materia_email and materia_email == email:
            return True

    if docente_titular and docente_nombres_coinciden(
        docente_nombre_materia,
        docente_titular.nombre,
    ):
        return True

    return False
