import grpc
import os
import django
from concurrent import futures
import logging

# Configurar Django antes de importar modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from proto_generated import alumnos_pb2_grpc
from grpc_server.servicer import AlumnosServicer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def serve():
    """Inicia el servidor gRPC en el puerto 50053."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    alumnos_pb2_grpc.add_AlumnosServiceServicer_to_server(AlumnosServicer(), server)
    
    port = '50053'
    server.add_insecure_port(f'[::]:{port}')
    logger.info(f"gRPC server listening on 0.0.0.0:{port}")
    
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("gRPC server stopping...")
        server.stop(0)

if __name__ == '__main__':
    serve()
