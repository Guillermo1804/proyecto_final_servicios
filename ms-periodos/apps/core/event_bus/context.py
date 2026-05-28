"""Contexto de trazabilidad para eventos."""

from __future__ import annotations

import contextvars
import uuid
from typing import Optional

_correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)
_causation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "causation_id", default=None
)


def get_correlation_id() -> str:
    value = _correlation_id.get()
    if not value:
        value = str(uuid.uuid4())
        _correlation_id.set(value)
    return value


def set_correlation_id(value: str) -> contextvars.Token:
    return _correlation_id.set(value)


def get_causation_id() -> Optional[str]:
    return _causation_id.get()


def set_causation_id(value: str) -> contextvars.Token:
    return _causation_id.set(value)


def reset_correlation_id(token: contextvars.Token) -> None:
    _correlation_id.reset(token)
