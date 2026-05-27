"""Consumidor de eventos de dominio para MS-1."""

from __future__ import annotations

import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from agm_events.config import EventBusConfig
from agm_events.consumer import EventConsumer
from agm_events.envelope import EventEnvelope
from agm_events.exceptions import BrokerConnectionError

from apps.core.event_bus.consumers import handle_user_create_requested

logger = logging.getLogger(__name__)

HANDLERS = {
    "user.create_requested.v1": handle_user_create_requested,
}


class Command(BaseCommand):
    help = "Consume eventos de la cola ms-auth.events"

    def add_arguments(self, parser):
        parser.add_argument("--poll-seconds", type=float, default=1.0)

    def handle(self, *args, **options):
        if not settings.USE_EVENT_BUS:
            self.stderr.write("USE_EVENT_BUS=false — consumer detenido.")
            return

        bus_config = EventBusConfig.from_env()
        queue_name = getattr(settings, "EVENT_QUEUE_NAME", "ms-auth.events")
        routing_keys = ["user.create_requested.v1"]

        consumer = EventConsumer(
            bus_config,
            queue_name=queue_name,
            routing_keys=routing_keys,
        )

        self.stdout.write(self.style.NOTICE(f"Consumer MS-1 en cola {queue_name}"))

        def _handler(envelope: EventEnvelope, _method) -> None:
            handler_fn = HANDLERS.get(envelope.event_name)
            if not handler_fn:
                logger.warning("unhandled_event", extra={"event_name": envelope.event_name})
                return
            handler_fn(envelope)

        while True:
            try:
                consumer.setup_topology()
                consumed = consumer.consume_one(_handler, timeout_seconds=5.0)
                if not consumed:
                    time.sleep(options["poll_seconds"])
            except BrokerConnectionError as exc:
                self.stderr.write(self.style.ERROR(f"Broker: {exc}"))
                time.sleep(5)
            except KeyboardInterrupt:
                consumer.close()
                break
