"""Consumidor RabbitMQ MS-4 — cola ms-calificaciones.events + DLQ."""

from __future__ import annotations

import logging
import time

import pika
from django.conf import settings
from django.core.management.base import BaseCommand

from agm_events.config import EventBusConfig
from agm_events.envelope import EventEnvelope
from agm_events.exceptions import BrokerConnectionError, EventValidationError

from apps.core.event_bus.consumers import HANDLERS

logger = logging.getLogger(__name__)

ROUTING_KEYS = [
    'user.created.v1',
    'user.updated.v1',
    'periodo.created.v1',
    'periodo.updated.v1',
    'periodo.closed.v1',
    'materia.created.v1',
    'materia.updated.v1',
    'materia.assigned_teacher.v1',
    'materia.closed.v1',
    'alumno.imported.v1',
    'alumno.updated.v1',
    'alumno.withdrawn.v1',
]


class Command(BaseCommand):
    help = 'Consume eventos upstream para proyecciones MS-4 (Fase 6)'

    def add_arguments(self, parser):
        parser.add_argument('--poll-seconds', type=float, default=1.0)

    def handle(self, *args, **options):
        if not settings.USE_EVENT_BUS:
            self.stderr.write('USE_EVENT_BUS=false — consumer detenido.')
            return

        bus_config = EventBusConfig.from_env()
        queue_name = getattr(settings, 'EVENT_QUEUE_NAME', 'ms-calificaciones.events')
        retry_queue = f'{queue_name}.retry'
        dlq_queue = f'{queue_name}.dlq'

        self.stdout.write(
            self.style.NOTICE(
                f'MS-4 consumer → {queue_name} @ {bus_config.exchange} '
                f'({bus_config.host}:{bus_config.port})'
            )
        )

        connection = None
        while True:
            try:
                connection = pika.BlockingConnection(bus_config.connection_parameters())
                channel = connection.channel()
                self._setup_topology(
                    channel, bus_config.exchange, queue_name, retry_queue, dlq_queue
                )
                method, properties, body = channel.basic_get(queue=queue_name, auto_ack=False)
                if method is None:
                    connection.sleep(options['poll_seconds'])
                    continue

                try:
                    envelope = EventEnvelope.from_json_bytes(body)
                    handler_fn = HANDLERS.get(envelope.event_name)
                    if not handler_fn:
                        logger.warning(
                            'unhandled_routing',
                            extra={'event_name': envelope.event_name},
                        )
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                        continue
                    try:
                        handler_fn(envelope)
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                    except EventValidationError as exc:
                        logger.error(
                            'schema_validation_failed',
                            extra={
                                'event_id': str(envelope.event_id),
                                'error': str(exc),
                            },
                        )
                        channel.basic_publish(exchange='', routing_key=dlq_queue, body=body)
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                except EventValidationError as exc:
                    logger.error('envelope_invalid', extra={'error': str(exc)})
                    channel.basic_publish(exchange='', routing_key=dlq_queue, body=body)
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    logger.exception('handler_failed')
                    retry_count = self._retry_count(properties)
                    if retry_count >= bus_config.consume_max_retries:
                        channel.basic_publish(exchange='', routing_key=dlq_queue, body=body)
                    else:
                        channel.basic_publish(
                            exchange='',
                            routing_key=retry_queue,
                            body=body,
                            properties=pika.BasicProperties(
                                headers={'x-retry-count': retry_count + 1},
                            ),
                        )
                    channel.basic_ack(delivery_tag=method.delivery_tag)
            except BrokerConnectionError as exc:
                self.stderr.write(self.style.ERROR(f'Broker: {exc}'))
                time.sleep(5)
            except KeyboardInterrupt:
                if connection and connection.is_open:
                    connection.close()
                break
            finally:
                if connection and connection.is_open:
                    try:
                        connection.close()
                    except Exception:
                        pass

    def _setup_topology(
        self, channel, exchange: str, queue_name: str, retry_queue: str, dlq_queue: str
    ) -> None:
        channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_declare(
            queue=retry_queue,
            durable=True,
            arguments={
                'x-message-ttl': 30000,
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': queue_name,
            },
        )
        channel.queue_declare(queue=dlq_queue, durable=True)
        for key in ROUTING_KEYS:
            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=key)
        channel.basic_qos(prefetch_count=1)

    def _retry_count(self, properties) -> int:
        if properties and properties.headers:
            return int(properties.headers.get('x-retry-count', 0))
        return 0
