import logging
import os
import sys
from concurrent import futures

import django
import grpc
from decouple import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'proto_generated'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def serve():
    """Arranca el servidor gRPC de MS-7."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    from grpc_server.servicer import ReportesServicer
    from proto_generated import reportes_pb2_grpc

    max_workers = config('GRPC_MAX_WORKERS', default=10, cast=int)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    reportes_pb2_grpc.add_ReportesServiceServicer_to_server(ReportesServicer(), server)

    port = config('GRPC_PORT', default='50057')
    server.add_insecure_port(f'0.0.0.0:{port}')
    server.start()
    logger.info('[MS-7] gRPC server listening on 0.0.0.0:%s', port)
    print(f'[MS-7] gRPC server listening on 0.0.0.0:{port}', flush=True)
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
