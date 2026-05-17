"""Canales gRPC reutilizables (singleton por servicio upstream)."""

import grpc
from decouple import config

GRPC_TIMEOUT_SECONDS = 5

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


def grpc_timeout() -> float:
    return float(config('GRPC_CLIENT_TIMEOUT', default=GRPC_TIMEOUT_SECONDS))
