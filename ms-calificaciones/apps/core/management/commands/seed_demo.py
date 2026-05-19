"""Ponderaciones, actividades y calificaciones demo."""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Actividad, Calificacion, Ponderacion


RUBROS = [
    ('Tareas', Decimal('30')),
    ('Examen parcial', Decimal('30')),
    ('Proyecto final', Decimal('40')),
]

ACTIVIDADES = [
    ('Tarea 1 — HTML/CSS', 0),
    ('Tarea 2 — JavaScript', 0),
    ('Parcial 1', 1),
    ('Proyecto Angular', 2),
]

NOTAS = {
    1: ['9.0', '8.5', '8.0', '9.5'],
    2: ['7.0', '7.5', '6.5', '8.0'],
    3: ['10.0', '9.5', '9.0', '10.0'],
    4: ['6.0', '6.5', '5.5', '7.0'],
    5: ['8.0', '8.0', '7.0', '8.5'],
    6: ['5.5', '6.0', '5.0', '6.5'],
}


def _seed_materia(materia_id: int, alumno_ids: list[int]) -> None:
    ponderacion_ids = []
    for nombre, pct in RUBROS:
        pond, _ = Ponderacion.objects.update_or_create(
            materia_id=materia_id,
            nombre_categoria=nombre,
            defaults={'porcentaje': pct},
        )
        ponderacion_ids.append(pond.id)

    actividad_ids = []
    for act_nombre, rubro_idx in ACTIVIDADES:
        act, _ = Actividad.objects.update_or_create(
            ponderacion_id=ponderacion_ids[rubro_idx],
            nombre=act_nombre,
            defaults={'descripcion': f'Demo {act_nombre}'},
        )
        actividad_ids.append(act.id)

    for idx, alumno_id in enumerate(alumno_ids):
        grades = NOTAS.get(idx + 1, ['7.0', '7.0', '7.0', '7.0'])
        for act_id, grade in zip(actividad_ids, grades):
            Calificacion.objects.update_or_create(
                actividad_id=act_id,
                alumno_id=alumno_id,
                defaults={'calificacion': Decimal(grade)},
            )


class Command(BaseCommand):
    help = 'Crea plan de evaluación y notas demo (idempotente)'

    def add_arguments(self, parser):
        parser.add_argument('--materia-ids', type=str, default='1,2,3')
        parser.add_argument('--alumno-ids', type=str, default='1,2,3,4,5,6')

    @transaction.atomic
    def handle(self, *args, **options):
        materia_ids = [int(x) for x in options['materia_ids'].split(',') if x.strip()]
        alumno_ids = [int(x) for x in options['alumno_ids'].split(',') if x.strip()]

        for materia_id in materia_ids:
            ids = alumno_ids if materia_id == materia_ids[0] else alumno_ids[:3]
            _seed_materia(materia_id, ids)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Materia {materia_id}: {len(ids)} alumnos con calificaciones'
                )
            )
