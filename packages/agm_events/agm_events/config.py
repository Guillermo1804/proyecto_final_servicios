"""Configuracion del bus desde variables de entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_env() -> None:
    """Carga .env de la raiz del monorepo si existe."""
    root = _repo_root()
    env_file = root / ".env"
    example = root / ".env.example"
    if env_file.is_file():
        load_dotenv(env_file)
    elif example.is_file():
        load_dotenv(example)


@dataclass(frozen=True)
class EventBusConfig:
    host: str
    port: int
    user: str
    password: str
    vhost: str
    exchange: str
    publish_retries: int
    publish_backoff_seconds: float
    consume_max_retries: int
    prefetch_count: int

    @classmethod
    def from_env(cls, *, load_dotenv_file: bool = True) -> EventBusConfig:
        if load_dotenv_file:
            load_env()
        return cls(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            user=os.getenv("RABBITMQ_USER", "agm_bus"),
            password=os.getenv("RABBITMQ_PASSWORD", "agm_bus_dev_change_me"),
            vhost=os.getenv("RABBITMQ_VHOST", "agm"),
            exchange=os.getenv("EVENT_EXCHANGE", "agm.domain"),
            publish_retries=int(os.getenv("EVENT_PUBLISH_RETRIES", "5")),
            publish_backoff_seconds=float(os.getenv("EVENT_PUBLISH_BACKOFF_SECONDS", "2")),
            consume_max_retries=int(os.getenv("EVENT_CONSUME_MAX_RETRIES", "5")),
            prefetch_count=int(os.getenv("EVENT_CONSUME_PREFETCH", "10")),
        )

    def amqp_url(self) -> str:
        from urllib.parse import quote

        vhost = quote(self.vhost, safe="")
        return (
            f"amqp://{quote(self.user, safe='')}:{quote(self.password, safe='')}"
            f"@{self.host}:{self.port}/{vhost}"
        )

    def connection_parameters(self) -> "pika.ConnectionParameters":
        import pika

        credentials = pika.PlainCredentials(self.user, self.password)
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=30,
            connection_attempts=1,
            retry_delay=0,
        )
