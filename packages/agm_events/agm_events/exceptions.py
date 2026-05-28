"""Excepciones del bus de eventos AGM."""


class EventBusError(Exception):
    """Error base del bus de eventos."""


class EventValidationError(EventBusError):
    """El sobre o payload no cumple el contrato JSON Schema."""


class BrokerConnectionError(EventBusError):
    """No se pudo conectar o operar con RabbitMQ."""


class DuplicateEventError(EventBusError):
    """El event_id ya fue procesado (inbox)."""


class PublishError(EventBusError):
    """Fallo al publicar tras reintentos."""


class ConsumerSetupError(EventBusError):
    """Error al declarar exchange/colas/bindings."""
