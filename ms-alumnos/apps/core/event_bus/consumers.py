"""Handlers del consumidor MS-3 (revocación JWT en cache local)."""

from __future__ import annotations

from agm_events.envelope import EventEnvelope


def handle_token_revoked(envelope: EventEnvelope) -> None:
    from agm_events.token_revoked import handle_token_revoked as _apply

    _apply(envelope)


HANDLERS = {
    'token.revoked.v1': handle_token_revoked,
}
