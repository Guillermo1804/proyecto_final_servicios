"""Eventos de dominio password -> outbox (MS-1)."""

from __future__ import annotations

from apps.core.event_bus.outbox import enqueue_domain_event


def enqueue_password_reset_requested(
    *,
    email: str,
    reset_url: str,
    token: str = '',
    nombre: str = '',
) -> None:
    enqueue_domain_event(
        event_name='password.reset_requested.v1',
        aggregate_type='password',
        aggregate_id=email,
        payload={
            'email': email,
            'reset_url': reset_url,
            'token': token,
            'nombre': nombre,
        },
    )
