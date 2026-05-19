"""Comprueba conectividad gRPC a MS-2/4/5 (sin mocks)."""

from django.core.management.base import BaseCommand

from grpc_clients.calificaciones_client import get_concentrado, use_mock_data
from grpc_clients.asistencias_client import get_estadisticas_asistencia
from grpc_clients.exceptions import MateriaNotFound
from grpc_clients.periodos_client import get_materias_by_docente


class Command(BaseCommand):
    help = 'Verifica que USE_MOCK_DATA=False y los upstreams gRPC responden.'

    def add_arguments(self, parser):
        parser.add_argument('--materia-id', type=int, default=1)
        parser.add_argument('--docente-usuario-id', type=int, default=2)

    def handle(self, *args, **options):
        materia_id = options['materia_id']
        docente_id = options['docente_usuario_id']

        if use_mock_data():
            self.stderr.write(
                self.style.ERROR('USE_MOCK_DATA=True — activar False en .env para datos reales')
            )
            return

        self.stdout.write(self.style.SUCCESS('USE_MOCK_DATA=False'))

        materias = get_materias_by_docente(docente_id)
        self.stdout.write(f'MS-2 materias docente {docente_id}: {len(materias.materias)}')

        try:
            conc = get_concentrado(materia_id)
            self.stdout.write(
                f'MS-4 concentrado materia {materia_id}: {len(conc.alumnos)} alumnos'
            )
        except MateriaNotFound as exc:
            self.stdout.write(
                self.style.WARNING(
                    f'MS-4 respondió (sin datos locales para materia {materia_id}): {exc}'
                )
            )

        try:
            stats = get_estadisticas_asistencia(materia_id)
            self.stdout.write(
                f'MS-5 asistencias materia {materia_id}: '
                f'{stats.porcentaje_asistencia_grupal:.1f}% asistencia grupal'
            )
        except MateriaNotFound as exc:
            self.stdout.write(
                self.style.WARNING(f'MS-5 respondió sin stats: {exc}')
            )

        self.stdout.write(self.style.SUCCESS('Upstream gRPC alcanzable (sin mocks forzados)'))
