import os
import sys
from concurrent import futures
import grpc
import django

# Añadir el directorio raíz y proto_generated al path para que apps.* y stubs sean importables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "proto_generated"))

def serve():
    """Configura y arranca el servidor gRPC."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    # Importar el servicer y stubs después de django.setup()
    from grpc_server.servicer import PeriodosServicer
    from proto_generated import periodos_pb2_grpc

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    periodos_pb2_grpc.add_PeriodosServiceServicer_to_server(
        PeriodosServicer(), server
    )

    port = os.getenv("GRPC_PORT", "50052")
    server.add_insecure_port(f"0.0.0.0:{port}")
    
    print(f"gRPC server listening on 0.0.0.0:{port}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
