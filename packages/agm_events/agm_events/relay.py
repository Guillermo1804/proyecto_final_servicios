"""Relay outbox → RabbitMQ (worker sincrono de referencia)."""

from __future__ import annotations

import json
import logging

from agm_events.envelope import EventEnvelope
from agm_events.outbox import OutboxStore
from agm_events.publisher import EventPublisher

logger = logging.getLogger(__name__)


def relay_pending_outbox(outbox: OutboxStore, publisher: EventPublisher) -> int:
    """
    Publica todos los registros pending y los marca published.
    Returns cantidad publicada.
    """
    published = 0
    for record in outbox.list_pending():
        envelope = EventEnvelope.from_dict(json.loads(record.payload_json))
        publisher.publish(envelope)
        outbox.mark_published(record.event_id)
        published += 1
        logger.info("outbox_relayed", extra={"event_id": record.event_id})
    return published
