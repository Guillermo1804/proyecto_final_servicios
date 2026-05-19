# Este archivo se mantiene por compatibilidad histórica.
# Las implementaciones reales están en grpc_clients/__init__.py
from grpc_clients import (
    alumnos_channel,
    auth_channel,
    periodos_channel,
    get_alumno_by_id,
    validate_token,
    get_materia_by_id,
)

__all__ = [
    'alumnos_channel',
    'auth_channel',
    'periodos_channel',
    'get_alumno_by_id',
    'validate_token',
    'get_materia_by_id',
]
