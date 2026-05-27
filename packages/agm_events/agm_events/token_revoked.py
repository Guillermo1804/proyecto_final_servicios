"""Handler reutilizable para token.revoked.v1."""

from __future__ import annotations

from agm_events.envelope import EventEnvelope
from agm_events.jwt_revocation import apply_token_revoked_payload


def handle_token_revoked(envelope: EventEnvelope) -> None:
    apply_token_revoked_payload(envelope.payload)
