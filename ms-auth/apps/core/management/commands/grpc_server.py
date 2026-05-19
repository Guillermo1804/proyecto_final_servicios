import grpc
from concurrent import futures
from django.core.management.base import BaseCommand
from decouple import config
from proto_generated import auth_pb2_grpc

from apps.core.grpc_servicer import AuthServiceServicer


class Command(BaseCommand):
    help = 'Inicia el servidor gRPC de autenticación'

    def handle(self, *args, **options):
        grpc_port = config('GRPC_PORT', default='50051')
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
        server.add_insecure_port(f'0.0.0.0:{grpc_port}')
        server.start()
        self.stdout.write(self.style.SUCCESS(f'Servidor gRPC iniciado en puerto {grpc_port}'))
        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            server.stop(0)
            self.stdout.write(self.style.SUCCESS('Servidor gRPC detenido'))
