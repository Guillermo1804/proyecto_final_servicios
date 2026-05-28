"""Publicador sincrono hacia el exchange agm.domain."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika import BasicProperties

from agm_events.config import EventBusConfig
from agm_events.envelope import EventEnvelope
from agm_events.exceptions import BrokerConnectionError, PublishError
from agm_events.validation import validate_full_event

if TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingConnection

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publica envelopes JSON en un exchange topic durable."""

    def __init__(
        self,
        config: EventBusConfig,
        *,
        connection: BlockingConnection | None = None,
        own_connection: bool = True,
    ) -> None:
        self._config = config
        self._connection = connection
        self._own_connection = own_connection and connection is None
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

    def __enter__(self) -> EventPublisher:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _ensure_channel(self) -> BlockingChannel:
        if self._connection is None or not self._connection.is_open:
            self.connect()
        assert self._connection is not None
        if self._channel is None or not self._channel.is_open:
            self._channel = self._connection.channel()
            self._channel.exchange_declare(
                exchange=self._config.exchange,
                exchange_type="topic",
                durable=True,
            )
        return self._channel

    def publish(
        self,
        envelope: EventEnvelope,
        *,
        validate: bool = True,
        mandatory: bool = False,
    ) -> None:
        if validate:
            validate_full_event(envelope)

        routing_key = envelope.event_name
        body = envelope.to_json_bytes()
        last_error: Exception | None = None

        for attempt in range(1, self._config.publish_retries + 1):
            try:
                channel = self._ensure_channel()
                channel.basic_publish(
                    exchange=self._config.exchange,
                    routing_key=routing_key,
                    body=body,
                    properties=BasicProperties(
                        content_type="application/json",
                        delivery_mode=2,
                        message_id=envelope.event_id,
                        correlation_id=envelope.correlation_id,
                        headers={
                            "event_name": envelope.event_name,
                            "source_service": envelope.source_service,
                        },
                    ),
                    mandatory=mandatory,
                )
                logger.info(
                    "event_published",
                    extra={
                        "event_id": envelope.event_id,
                        "correlation_id": envelope.correlation_id,
                        "event_name": envelope.event_name,
                        "routing_key": routing_key,
                    },
                )
                return
            except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError) as exc:
                last_error = exc
                self.close()
                if attempt >= self._config.publish_retries:
                    break
                sleep_s = self._config.publish_backoff_seconds * attempt
                logger.warning(
                    "publish_retry",
                    extra={"attempt": attempt, "sleep_seconds": sleep_s, "error": str(exc)},
                )
                time.sleep(sleep_s)

        raise PublishError(
            f"Failed to publish {envelope.event_name} after {self._config.publish_retries} attempts"
        ) from last_error
