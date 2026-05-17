"""Canales gRPC reutilizables (singleton por servicio upstream)."""

import grpc
from decouple import config

DEFAULT_GRPC_TIMEOUT = 5.0
DEFAULT_CALIFICACIONES_TIMEOUT = 30.0

_channels: dict[str, grpc.Channel] = {}


def get_channel(
    service_key: str,
    host_var: str,
    port_var: str,
    default_host: str,
    default_port: str,
) -> grpc.Channel:
    host = config(host_var, default=default_host)
    port = config(port_var, default=default_port)
    target = f'{host}:{port}'
    if service_key not in _channels:
        _channels[service_key] = grpc.insecure_channel(target)
    return _channels[service_key]


def clear_channels() -> None:
    """Cierra y elimina canales cacheados (tests)."""
    for channel in _channels.values():
        channel.close()
    _channels.clear()


def grpc_timeout() -> float:
    return float(config('GRPC_CLIENT_TIMEOUT', default=DEFAULT_GRPC_TIMEOUT))


def calificaciones_grpc_timeout() -> float:
    return float(
        config('GRPC_CLIENT_TIMEOUT_CALIFICACIONES', default=DEFAULT_CALIFICACIONES_TIMEOUT)
    )
