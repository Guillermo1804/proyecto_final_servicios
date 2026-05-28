"""Worker outbox MS-3 → RabbitMQ."""

from __future__ import annotations

import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from agm_events.config import EventBusConfig
from agm_events.envelope import build_envelope
from agm_events.exceptions import BrokerConnectionError, PublishError
from agm_events.publisher import EventPublisher

from apps.core.models import EventOutbox

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Relay continuo: event_outbox (pending) → exchange agm.domain"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--batch-size", type=int, default=50)
        parser.add_argument("--poll-seconds", type=float, default=2.0)

    def handle(self, *args, **options):
        if not settings.USE_EVENT_BUS:
            self.stderr.write("USE_EVENT_BUS=false — worker detenido.")
            return

        bus_config = EventBusConfig.from_env()
        self.stdout.write(
            self.style.NOTICE(
                f"MS-3 outbox relay → {bus_config.exchange} @ {bus_config.host}:{bus_config.port}"
            )
        )

        while True:
            published = self._relay_batch(bus_config, options["batch_size"])
            if options["once"]:
                break
            time.sleep(options["poll_seconds"] if published == 0 else 0.1)

    def _relay_batch(self, bus_config: EventBusConfig, batch_size: int) -> int:
        rows = list(
            EventOutbox.objects.filter(status=EventOutbox.Status.PENDING).order_by(
                "created_at"
            )[:batch_size]
        )
        if not rows:
            return 0

        published_count = 0
        try:
            with EventPublisher(bus_config) as publisher:
                for row in rows:
                    if self._publish_row(publisher, bus_config, row):
                        published_count += 1
        except BrokerConnectionError as exc:
            logger.error("outbox_relay_broker_down", extra={"error": str(exc)})
            self.stderr.write(self.style.ERROR(f"Broker no disponible: {exc}"))
            return 0
        return published_count

    def _publish_row(
        self, publisher: EventPublisher, bus_config: EventBusConfig, row: EventOutbox
    ) -> bool:
        raw_payload = dict(row.payload or {})
        meta = raw_payload.pop("_agm_meta", {}) or {}
        envelope = build_envelope(
            event_id=str(row.event_id),
            event_name=row.event_name,
            event_version=row.event_version,
            aggregate_type=row.aggregate_type,
            aggregate_id=row.aggregate_id,
            source_service=getattr(settings, "SERVICE_NAME", "ms-alumnos"),
            payload=raw_payload,
            correlation_id=meta.get("correlation_id") or str(row.event_id),
            causation_id=meta.get("causation_id") or str(row.event_id),
        )
        try:
            publisher.publish(envelope)
        except PublishError as exc:
            row.retry_count += 1
            row.last_error = str(exc)[:2000]
            if row.retry_count >= bus_config.publish_retries:
                row.status = EventOutbox.Status.FAILED
            row.save(update_fields=["retry_count", "last_error", "status"])
            return False

        with transaction.atomic():
            row.status = EventOutbox.Status.PUBLISHED
            row.processed_at = timezone.now()
            row.last_error = None
            row.save(update_fields=["status", "processed_at", "last_error"])

        self.stdout.write(
            self.style.SUCCESS(
                f"published event_id={row.event_id} event_name={row.event_name} status=published"
            )
        )
        return True
