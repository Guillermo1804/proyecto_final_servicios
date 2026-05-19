"""Periodo activo y materias demo para docente."""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Materia, Periodo


class Command(BaseCommand):
    help = 'Crea periodo activo y materias demo (idempotente)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--docente-usuario-id',
            type=int,
            default=0,
            help='usuario_id del docente en MS-1 (titular de materias)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        docente_id = options['docente_usuario_id'] or None
        if not docente_id:
            self.stderr.write('Indique --docente-usuario-id (salida de seed_demo_users en MS-1).')
            return

        Periodo.objects.filter(activo=True).update(activo=False)

        periodo, _ = Periodo.objects.update_or_create(
            nombre='2026-1 Primavera Demo',
            defaults={
                'fecha_inicio': date(2026, 1, 15),
                'fecha_fin': date(2026, 6, 30),
                'plan_estudios': 'ICC 2020',
                'activo': True,
            },
        )
        periodo.activo = True
        periodo.save(update_fields=['activo', 'fecha_actualizacion'])

        periodo_pasado, _ = Periodo.objects.update_or_create(
            nombre='2025-2 Otoño Demo',
            defaults={
                'fecha_inicio': date(2025, 8, 1),
                'fecha_fin': date(2025, 12, 15),
                'plan_estudios': 'ICC 2020',
                'activo': False,
            },
        )

        materias_spec = [
            ('12345', 'Programación Web', '01', 'PW-301', 'Lun-Mié 08:00-10:00'),
            ('12346', 'Bases de Datos', '01', 'BD-302', 'Mar-Jue 10:00-12:00'),
            ('12347', 'Ingeniería de Software', '01', 'IS-401', 'Vie 08:00-11:00'),
        ]
        materia_ids = []
        for nrc, nombre, seccion, clave, horario in materias_spec:
            materia, _ = Materia.objects.update_or_create(
                periodo=periodo,
                nrc=nrc,
                defaults={
                    'nombre': nombre,
                    'seccion': seccion,
                    'clave': clave,
                    'docente_nombre': 'María Docente Demo',
                    'docente_id': docente_id,
                    'horario': horario,
                },
            )
            materia_ids.append(materia.id)
            self.stdout.write(f'Materia {materia.id}: {nrc} {nombre}')

        Materia.objects.update_or_create(
            periodo=periodo_pasado,
            nrc='99001',
            defaults={
                'nombre': 'Matemáticas Discretas (archivo)',
                'seccion': '01',
                'clave': 'MD-201',
                'docente_nombre': 'María Docente Demo',
                'docente_id': docente_id,
                'horario': '—',
            },
        )

        self.stdout.write(self.style.SUCCESS(f'Periodo activo id={periodo.id}'))
        self.stdout.write(f'SEED_PERIODO_ID={periodo.id}')
        self.stdout.write(f'SEED_MATERIA_IDS={",".join(str(i) for i in materia_ids)}')
