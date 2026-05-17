import grpc
from decouple import config

from proto_generated import auth_pb2_grpc


def get_auth_stub():
    """
    Crea y retorna un stub de AuthService para comunicación gRPC con MS-1.
    Host/port configurados vía variables de entorno.
    """
    host = config("MS_AUTH_GRPC_HOST", default="ms-auth")
    port = config("MS_AUTH_GRPC_PORT", default="50051")
    channel = grpc.insecure_channel(f"{host}:{port}")
    return auth_pb2_grpc.AuthServiceStub(channel)
