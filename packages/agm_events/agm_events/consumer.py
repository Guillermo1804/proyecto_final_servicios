"""Consumidor base sincrono con declaracion de cola y bindings."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import pika
from pika.adapters.blocking_connection import BlockingChannel

from agm_events.config import EventBusConfig
from agm_events.envelope import EventEnvelope
from agm_events.exceptions import BrokerConnectionError, ConsumerSetupError
from agm_events.validation import validate_full_event

if TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingConnection
    from pika.spec import Basic

logger = logging.getLogger(__name__)

MessageHandler = Callable[[EventEnvelope, "Basic.Deliver"], None]


class EventConsumer:
    """Consume mensajes de una cola durable con ack manual."""

    def __init__(
        self,
        config: EventBusConfig,
        *,
        queue_name: str,
        routing_keys: list[str],
        connection: BlockingConnection | None = None,
    ) -> None:
        self._config = config
        self._queue_name = queue_name
        self._routing_keys = routing_keys
        self._connection = connection
        self._own_connection = connection is None
        self._channel: BlockingChannel | None = None

    def connect(self) -> None:
        if self._connection is not None and self._connection.is_open:
            return
        try:
            self._connection = pika.BlockingConnection(self._config.connection_parameters())
            self._own_connection = True
        except pika.exceptions.AMQPConnectionError as exc:
            raise BrokerConnectionError(f"Cannot connect to RabbitMQ: {exc}") from exc

    def close(self) -> None:
        try:
            if self._channel is not None and self._channel.is_open:
                self._channel.close()
        finally:
            self._channel = None
        if self._own_connection and self._connection is not None:
            try:
                if self._connection.is_open:
                    self._connection.close()
            finally:
                self._connection = None

    def __enter__(self) -> EventConsumer:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def setup_topology(self) -> None:
        """Declara exchange, cola durable y bindings."""
        if self._connection is None or not self._connection.is_open:
            self.connect()
        assert self._connection is not None
        try:
            channel = self._connection.channel()
            channel.exchange_declare(
                exchange=self._config.exchange,
                exchange_type="topic",
                durable=True,
            )
            channel.queue_declare(queue=self._queue_name, durable=True)
            for key in self._routing_keys:
                channel.queue_bind(
                    exchange=self._config.exchange,
                    queue=self._queue_name,
                    routing_key=key,
                )
            channel.basic_qos(prefetch_count=self._config.prefetch_count)
            self._channel = channel
        except pika.exceptions.AMQPError as exc:
            raise ConsumerSetupError(f"Failed to setup consumer topology: {exc}") from exc

    def consume_one(
        self,
        handler: MessageHandler,
        *,
        validate: bool = True,
        timeout_seconds: float = 30.0,
    ) -> bool:
        """
        Consume un unico mensaje con timeout (basic_get sincrono).
        Returns True si se proceso un mensaje, False si hubo timeout.
        """
        if self._channel is None:
            self.setup_topology()
        assert self._channel is not None

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            method, _properties, body = self._channel.basic_get(
                queue=self._queue_name,
                auto_ack=False,
            )
            if method is None:
                time.sleep(0.25)
                self._connection.process_data_events(time_limit=0)
                continue
            try:
                envelope = EventEnvelope.from_json_bytes(body)
                if validate:
                    validate_full_event(envelope)
                handler(envelope, method)
                self._channel.basic_ack(delivery_tag=method.delivery_tag)
                return True
            except Exception:
                self._channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                raise

        return False

    def purge_queue(self) -> int:
        """Elimina mensajes pendientes (solo pruebas)."""
        if self._channel is None:
            self.setup_topology()
        assert self._channel is not None
        result = self._channel.queue_purge(self._queue_name)
        return int(result.method.message_count)
