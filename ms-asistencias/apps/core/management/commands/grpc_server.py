import grpc
from concurrent import futures
import django
import os
from django.core.management.base import BaseCommand

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


class Command(BaseCommand):
    help = 'Inicia el servidor gRPC de asistencias'

    def handle(self, *args, **options):
        django.setup()

        from proto_generated import asistencias_pb2_grpc
        from grpc_server.servicer import AsistenciasServicer
        from decouple import config

        port = config('GRPC_PORT', default='50055')

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        asistencias_pb2_grpc.add_AsistenciasServiceServicer_to_server(
            AsistenciasServicer(), server
        )
        server.add_insecure_port(f'0.0.0.0:{port}')
        server.start()
        self.stdout.write(self.style.SUCCESS(f'✓ Servidor gRPC iniciado en puerto {port}'))

        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            server.stop(0)
            self.stdout.write(self.style.SUCCESS('✓ Servidor gRPC detenido'))
