"""Eventos de dominio relacionados con tokens."""

from __future__ import annotations

from apps.core.event_bus.outbox import enqueue_domain_event


def enqueue_token_revoked(*, user_id: int, jti: str, token_type: str = "refresh") -> None:
    enqueue_domain_event(
        event_name="token.revoked.v1",
        aggregate_type="token",
        aggregate_id=jti,
        payload={
            "user_id": user_id,
            "jti": jti,
            "token_type": token_type,
        },
        causation_id=jti,
    )
