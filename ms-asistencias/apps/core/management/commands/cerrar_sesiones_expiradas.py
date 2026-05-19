"""
Cierra sesiones activas cuya ventana de 10 min expiró o cuya clave Redis ya no existe.

Uso:
  python manage.py cerrar_sesiones_expiradas
  # Cron ejemplo (cada minuto):
  # * * * * * docker exec agm-ms-asistencias python manage.py cerrar_sesiones_expiradas
"""

from django.core.management.base import BaseCommand

from apps.core.models import SesionAsistencia
from apps.core.services import SesionAsistenciaService
from apps.core.utils import get_sesion_from_redis


class Command(BaseCommand):
    help = 'Cierra sesiones de asistencia expiradas (TTL Redis / ventana 10 min)'

    def handle(self, *args, **options):
        cerradas = 0
        omitidas = 0

        for sesion in SesionAsistencia.objects.filter(activa=True):
            redis_vivo = get_sesion_from_redis(sesion.id) is not None
            expirada = not sesion.esta_vigente()

            if expirada or not redis_vivo:
                ok, msg = SesionAsistenciaService.cerrar_sesion(sesion.id)
                if ok:
                    cerradas += 1
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    omitidas += 1
                    self.stdout.write(self.style.WARNING(msg))

        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso finalizado: {cerradas} sesión(es) cerrada(s), {omitidas} omitida(s).'
            )
        )
