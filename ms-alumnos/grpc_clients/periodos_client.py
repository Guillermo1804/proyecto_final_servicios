import os
import sys
import grpc
from decouple import config

# Dynamically add proto_generated to sys.path to avoid ModuleNotFoundError
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "proto_generated"))

from proto_generated import periodos_pb2_grpc

"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""
from agm_events.grpc_legacy import block_business_grpc


def get_periodos_stub():
    block_business_grpc('periodos_client.py.get_periodos_stub')
    """
    Crea y retorna un stub de PeriodosService para comunicación gRPC con MS-2.
    Host/port configurados vía variables de entorno.
    """
    host = config("MS_PERIODOS_GRPC_HOST", default="ms-periodos")
    port = config("MS_PERIODOS_GRPC_PORT", default="50052")
    channel = grpc.insecure_channel(f"{host}:{port}")
    return periodos_pb2_grpc.PeriodosServiceStub(channel)
