#!/usr/bin/env python3
"""
Fase 1 — Prueba de humo del bus AGM.
Requiere RabbitMQ accesible (docker compose up -d rabbitmq).
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

# Raiz del paquete en PYTHONPATH
_PKG_ROOT = Path(__file__).resolve().parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from agm_events.config import EventBusConfig, load_env
from agm_events.consumer import EventConsumer
from agm_events.envelope import EventEnvelope, build_envelope
from agm_events.exceptions import BrokerConnectionError, DuplicateEventError
from agm_events.inbox import InboxStore
from agm_events.outbox import OutboxStatus, OutboxStore
from agm_events.publisher import EventPublisher
from agm_events.relay import relay_pending_outbox
from agm_events.validation import validate_full_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("agm.smoke_test")

EVENT_NAME = "health.ping.v1"
QUEUE_NAME = os.getenv("SMOKE_TEST_QUEUE", "ms-smoke-test.events")
ROUTING_KEY = os.getenv("SMOKE_TEST_ROUTING_KEY", EVENT_NAME)


def _log_step(step: str, **fields: object) -> None:
    extras = " ".join(f"{k}={v}" for k, v in fields.items())
    logger.info("STEP %s %s", step, extras)


def _process_in_inbox(inbox: InboxStore, envelope: EventEnvelope, handler: str) -> bool:
    """Returns True si se proceso; False si duplicado."""
    if not inbox.try_register(envelope.event_id, envelope.event_name, handler):
        _log_step("inbox_duplicate_discarded", event_id=envelope.event_id)
        return False
    validate_full_event(envelope)
    _log_step(
        "inbox_stored",
        event_id=envelope.event_id,
        correlation_id=envelope.correlation_id,
        event_name=envelope.event_name,
    )
    return True


def step_publish_and_consume(
    config: EventBusConfig, inbox: InboxStore
) -> EventEnvelope:
    _log_step("1_publish_and_consume", status="start")
    event_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())

    envelope = build_envelope(
        event_id=event_id,
        correlation_id=correlation_id,
        event_name=EVENT_NAME,
        event_version=1,
        aggregate_type="health",
        aggregate_id="smoke-1",
        source_service="ms-smoke-test",
        payload={"message": "AGM Fase 1 smoke test"},
    )
    validate_full_event(envelope)

    processed_holder: list[bool] = []

    def handler(msg: EventEnvelope, _method: object) -> None:
        processed_holder.append(_process_in_inbox(inbox, msg, "health_ping_handler"))

    consumer = EventConsumer(
        config,
        queue_name=QUEUE_NAME,
        routing_keys=[ROUTING_KEY],
    )
    with EventPublisher(config) as publisher:
        try:
            consumer.purge_queue()
        except Exception:
            consumer.setup_topology()
        consumer.setup_topology()
        publisher.publish(envelope)
        _log_step(
            "published",
            event_id=envelope.event_id,
            correlation_id=envelope.correlation_id,
        )
        if not consumer.consume_one(handler, timeout_seconds=15.0):
            raise RuntimeError("Timeout waiting for health.ping.v1")
        if not processed_holder or not processed_holder[0]:
            raise RuntimeError("First message was not processed into inbox")
    consumer.close()
    _log_step("1_publish_and_consume", status="ok", event_id=event_id)
    return envelope


def step_duplicate(inbox: InboxStore, envelope: EventEnvelope) -> None:
    _log_step("2_idempotency", status="start", event_id=envelope.event_id)
    second = _process_in_inbox(inbox, envelope, "duplicate_replay")
    if second:
        raise RuntimeError("Expected duplicate event_id to be discarded")
    try:
        inbox.register(envelope.event_id, EVENT_NAME, "duplicate_forced")
        raise RuntimeError("register() should raise on duplicate")
    except DuplicateEventError:
        _log_step("2_idempotency", status="ok", event_id=envelope.event_id)
    assert inbox.count() == 1, "Inbox must contain exactly one row for event_id"


def step_broker_down_and_recovery(config: EventBusConfig, outbox: OutboxStore) -> None:
    _log_step("3_outbox_broker_recovery", status="start")
    recovery_id = str(uuid.uuid4())
    recovery_envelope = build_envelope(
        event_id=recovery_id,
        event_name=EVENT_NAME,
        event_version=1,
        aggregate_type="health",
        aggregate_id="smoke-recovery",
        source_service="ms-smoke-test",
        payload={"message": "outbox recovery after broker down"},
    )
    outbox.insert_pending(
        recovery_id,
        EVENT_NAME,
        recovery_envelope.to_dict(),
    )
    pending_before = outbox.count_by_status(OutboxStatus.PENDING)
    _log_step("outbox_pending_saved", event_id=recovery_id, pending_count=pending_before)

    bad_config = EventBusConfig(
        host="127.0.0.1",
        port=59999,
        user=config.user,
        password=config.password,
        vhost=config.vhost,
        exchange=config.exchange,
        publish_retries=1,
        publish_backoff_seconds=0.1,
        consume_max_retries=config.consume_max_retries,
        prefetch_count=config.prefetch_count,
    )
    publisher_bad = EventPublisher(bad_config)
    try:
        publisher_bad.publish(recovery_envelope)
        raise RuntimeError("Expected BrokerConnectionError")
    except BrokerConnectionError as exc:
        _log_step("broker_unreachable_caught", error=str(exc)[:120])

    assert outbox.get(recovery_id).status == OutboxStatus.PENDING

    with EventPublisher(config) as publisher_good:
        relay_pending_outbox(outbox, publisher_good)

    record = outbox.get(recovery_id)
    if record is None or record.status != OutboxStatus.PUBLISHED:
        raise RuntimeError(f"Expected published outbox, got {record}")
    _log_step(
        "3_outbox_broker_recovery",
        status="ok",
        event_id=recovery_id,
        published_at=record.published_at,
    )


def main() -> int:
    load_env()
    config = EventBusConfig.from_env(load_dotenv_file=False)

    _log_step("config", host=config.host, port=config.port, vhost=config.vhost, exchange=config.exchange)

    work_dir = Path(tempfile.mkdtemp(prefix="agm_smoke_"))
    outbox = OutboxStore(work_dir / "outbox.db")
    inbox = InboxStore(work_dir / "inbox.db")

    logger.info("SQLite workdir: %s", work_dir)

    # Esperar broker si acaba de levantar
    for attempt in range(1, 16):
        try:
            with EventPublisher(config) as pub:
                pub._ensure_channel()
            break
        except BrokerConnectionError:
            if attempt == 15:
                logger.error(
                    "RabbitMQ not reachable at %s:%s. Run: docker compose up -d rabbitmq",
                    config.host,
                    config.port,
                )
                return 1
            time.sleep(2)

    consumed_envelope = step_publish_and_consume(config, inbox)
    step_duplicate(inbox, consumed_envelope)
    step_broker_down_and_recovery(config, outbox)

    logger.info("=" * 60)
    logger.info("SMOKE TEST PASSED — Fase 1")
    logger.info("inbox_rows=%s outbox_published=%s", inbox.count(), outbox.count_by_status(OutboxStatus.PUBLISHED))
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
