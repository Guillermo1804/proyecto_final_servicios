"""
Utilidades Fase 9: bloqueo de clientes gRPC de negocio cuando USE_EVENT_BUS=true.

gRPC permitido solo para servidores entrantes de soporte/admin o herramientas
explicitamente documentadas en docs/CONTEXTO_GLOBAL_PROYECTO.md (regla R5).
"""

from __future__ import annotations

import functools
import os
import warnings
from typing import Callable, TypeVar

F = TypeVar('F', bound=Callable)


def event_bus_enabled() -> bool:
    raw = os.getenv('USE_EVENT_BUS', 'true').strip().lower()
    return raw in ('1', 'true', 'yes', 'on')


def block_business_grpc(operation: str) -> None:
    if event_bus_enabled():
        raise RuntimeError(
            f'gRPC de negocio deshabilitado (USE_EVENT_BUS=true): {operation}. '
            'Use RabbitMQ (outbox/inbox) y proyecciones locales.'
        )


def deprecated_business_grpc(operation: str) -> Callable[[F], F]:
    """Decorador: advierte en legacy y bloquea si el bus esta activo."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            block_business_grpc(operation)
            warnings.warn(
                f'[DEPRECATED] gRPC legacy: {operation}. Migrar a eventos.',
                DeprecationWarning,
                stacklevel=2,
            )
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
