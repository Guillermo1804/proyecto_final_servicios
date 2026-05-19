"""Sesiones y registros de asistencia demo."""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.core.models import RegistroAsistencia, SesionAsistencia


class Command(BaseCommand):
    help = 'Crea sesiones cerradas con asistencias demo (idempotente)'

    def add_arguments(self, parser):
        parser.add_argument('--materia-id', type=int, default=1)
        parser.add_argument('--docente-usuario-id', type=int, required=True)
        parser.add_argument('--alumno-ids', type=str, default='1,2,3,4,5,6')

    @transaction.atomic
    def handle(self, *args, **options):
        materia_id = options['materia_id']
        docente_id = options['docente_usuario_id']
        alumno_ids = [int(x) for x in options['alumno_ids'].split(',') if x.strip()]

        RegistroAsistencia.objects.filter(sesion__materia_id=materia_id).delete()
        SesionAsistencia.objects.filter(materia_id=materia_id).delete()

        now = timezone.now()
        n = len(alumno_ids)
        sesiones_data = [
            ('confirmada', alumno_ids),
            ('confirmada', alumno_ids[:-1] if n > 1 else list(alumno_ids)),
            ('cerrada', alumno_ids[: min(4, n)]),
        ]
        estados_alumno = ['presente', 'presente', 'retardo', 'presente', 'retardo', 'ausente']

        for idx, (estado_sesion, alumnos_sesion) in enumerate(sesiones_data, start=1):
            inicio = now - timezone.timedelta(days=10 - idx * 2)
            sesion = SesionAsistencia.objects.create(
                materia_id=materia_id,
                docente_id=docente_id,
                fecha_fin_teorica=inicio + timezone.timedelta(minutes=10),
                estado=estado_sesion,
                activa=False,
            )
            SesionAsistencia.objects.filter(pk=sesion.pk).update(fecha_inicio=inicio)

            for pos, alumno_id in enumerate(alumnos_sesion):
                estado_reg = estados_alumno[pos % len(estados_alumno)]
                RegistroAsistencia.objects.create(
                    sesion=sesion,
                    alumno_id=alumno_id,
                    estado=estado_reg,
                    minuto_registro=2 if estado_reg == 'presente' else 7,
                )
            self.stdout.write(f'Sesión {sesion.id} ({estado_sesion}): {len(alumnos_sesion)} registros')

        self.stdout.write(self.style.SUCCESS('Asistencias demo creadas.'))
