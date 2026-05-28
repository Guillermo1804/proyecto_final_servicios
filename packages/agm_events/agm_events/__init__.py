"""AGM event bus library — RabbitMQ, envelope, outbox/inbox."""

from agm_events.config import EventBusConfig
from agm_events.consumer import EventConsumer
from agm_events.envelope import EventEnvelope, build_envelope
from agm_events.exceptions import (
    BrokerConnectionError,
    DuplicateEventError,
    EventBusError,
    EventValidationError,
)
from agm_events.inbox import InboxRecord, InboxStore
from agm_events.outbox import OutboxRecord, OutboxStatus, OutboxStore
from agm_events.publisher import EventPublisher

__all__ = [
    "BrokerConnectionError",
    "DuplicateEventError",
    "EventBusConfig",
    "EventBusError",
    "EventConsumer",
    "EventEnvelope",
    "EventPublisher",
    "EventValidationError",
    "InboxRecord",
    "InboxStore",
    "OutboxRecord",
    "OutboxStatus",
    "OutboxStore",
    "build_envelope",
]

__version__ = "0.1.0"
