"""Cola interna SMTP desacoplada del ack de RabbitMQ."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from decouple import config

logger = logging.getLogger(__name__)

_executor: ThreadPoolExecutor | None = None


def get_mail_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        workers = config('EMAIL_MAX_WORKERS', default=4, cast=int)
        _executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='ms6-smtp')
    return _executor


def enqueue_mail_task(fn: Callable[[], None], *, event_id: str, event_name: str) -> None:
    """Encola envio SMTP; errores se registran en historial dentro de fn."""

    def _wrapped() -> None:
        try:
            logger.info(
                'smtp_dispatch_start',
                extra={'event_id': event_id, 'event_name': event_name},
            )
            fn()
            logger.info(
                'smtp_dispatch_done',
                extra={'event_id': event_id, 'event_name': event_name},
            )
        except Exception:
            logger.exception(
                'smtp_dispatch_failed',
                extra={'event_id': event_id, 'event_name': event_name},
            )

    get_mail_executor().submit(_wrapped)
