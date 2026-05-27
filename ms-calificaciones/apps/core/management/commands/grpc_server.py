import grpc
from concurrent import futures
import django
import os
from django.core.management.base import BaseCommand

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


class Command(BaseCommand):
    help = 'Inicia el servidor gRPC de calificaciones'

    def handle(self, *args, **options):
        django.setup()

        from proto_generated import calificaciones_pb2_grpc
        from grpc_server.servicer import CalificacionesServicer
        from decouple import config

        port = config('GRPC_PORT', default='50054')

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        calificaciones_pb2_grpc.add_CalificacionesServiceServicer_to_server(
            CalificacionesServicer(), server
        )
        server.add_insecure_port(f'0.0.0.0:{port}')
        server.start()
        self.stdout.write(self.style.SUCCESS(f'✓ Servidor gRPC iniciado en puerto {port}'))

        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            server.stop(0)
            self.stdout.write(self.style.SUCCESS('✓ Servidor gRPC detenido'))
