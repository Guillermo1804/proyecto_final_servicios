"""Carga inicial de MateriaProjection y AlumnoMateriaProjection."""

from __future__ import annotations

import logging

import MySQLdb
from decouple import config
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import (
    AlumnoMateriaProjection,
    Calificacion,
    DocenteProjection,
    MateriaProjection,
    Ponderacion,
)
from apps.core.event_bus import projection_service as proj

logger = logging.getLogger(__name__)


def _mysql_conn(prefix: str):
    host = config(f'{prefix}_HOST', default='')
    if not host:
        return None
    return MySQLdb.connect(
        host=host,
        port=int(config(f'{prefix}_PORT', default=3306)),
        user=config(f'{prefix}_USER', default='root'),
        passwd=config(f'{prefix}_PASSWORD', default='root_password'),
        db=config(f'{prefix}_NAME', default=''),
        charset='utf8mb4',
    )


class Command(BaseCommand):
    help = 'Backfill de proyecciones locales desde BD MS-2/MS-3 o datos existentes en MS-4'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-local-only',
            action='store_true',
            help='Solo inferir desde ponderaciones/calificaciones en MS-4',
        )

    def handle(self, *args, **options):
        materias = 0
        inscripciones = 0

        docentes = 0
        if not options['from_local_only']:
            materias += self._backfill_from_periodos()
            inscripciones += self._backfill_from_alumnos()
            docentes = self._backfill_docentes_from_alumnos()

        materias += self._backfill_from_local_calificaciones()
        inscripciones += self._backfill_inscripciones_from_local_grades()

        self.stdout.write(
            self.style.SUCCESS(
                f'Backfill completado: materias={materias}, inscripciones={inscripciones}, docentes={docentes}'
            )
        )

    def _backfill_from_periodos(self) -> int:
        conn = _mysql_conn('BACKFILL_PERIODOS_DB')
        if conn is None:
            self.stdout.write('BACKFILL_PERIODOS_DB_* no configurado — omitiendo MS-2')
            return 0
        count = 0
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT m.id, m.periodo_id, m.nrc, m.nombre, m.seccion, m.clave,
                       m.docente_nombre, m.docente_id, m.horario, p.nombre, p.activo
                FROM materias m
                JOIN periodos p ON p.id = m.periodo_id
                """
            )
            for row in cur.fetchall():
                proj.upsert_materia(
                    {
                        'materia_id': row[0],
                        'periodo_id': row[1],
                        'nrc': row[2] or '',
                        'nombre': row[3] or '',
                        'seccion': row[4] or '',
                        'clave': row[5] or '',
                        'horario': row[8] or '',
                        'docente_nombre': row[6] or '',
                        'docente_id': row[7],
                    },
                    periodo_nombre=row[9] or '',
                    periodo_activo=bool(row[10]),
                )
                count += 1
        finally:
            conn.close()
        return count

    def _backfill_from_alumnos(self) -> int:
        conn = _mysql_conn('BACKFILL_ALUMNOS_DB')
        if conn is None:
            self.stdout.write('BACKFILL_ALUMNOS_DB_* no configurado — omitiendo MS-3')
            return 0
        count = 0
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT i.alumno_id, i.materia_id, a.matricula,
                       CONCAT(a.nombre, ' ', a.apellido), a.email, i.activa
                FROM core_inscripcionmateria i
                JOIN core_alumno a ON a.id = i.alumno_id
                """
            )
            with transaction.atomic():
                for row in cur.fetchall():
                    proj.upsert_alumno_materia(
                        alumno_id=row[0],
                        materia_id=row[1],
                        matricula=row[2] or '',
                        nombre=(row[3] or '').strip(),
                        email=row[4] or '',
                        activa=bool(row[5]),
                    )
                    count += 1
        finally:
            conn.close()
        return count

    def _backfill_docentes_from_alumnos(self) -> int:
        conn = _mysql_conn('BACKFILL_ALUMNOS_DB')
        if conn is None:
            self.stdout.write('BACKFILL_ALUMNOS_DB_* no configurado — omitiendo docentes MS-3')
            return 0
        count = 0
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, usuario_id, email, nombre, apellido
                FROM core_docente
                """
            )
            for row in cur.fetchall():
                nombre = f"{row[3] or ''} {row[4] or ''}".strip()
                DocenteProjection.objects.update_or_create(
                    docente_id=row[0],
                    defaults={
                        'usuario_id': row[1],
                        'email': row[2] or '',
                        'nombre': nombre,
                    },
                )
                count += 1
        finally:
            conn.close()
        return count

    def _backfill_from_local_calificaciones(self) -> int:
        materia_ids = set(
            Ponderacion.objects.values_list('materia_id', flat=True).distinct()
        )
        count = 0
        for mid in materia_ids:
            if MateriaProjection.objects.filter(materia_id=mid).exists():
                continue
            MateriaProjection.objects.create(
                materia_id=mid,
                periodo_id=0,
                nrc=f'M{mid}',
                nombre=f'Materia {mid}',
            )
            count += 1
        return count

    def _backfill_inscripciones_from_local_grades(self) -> int:
        pairs = (
            Calificacion.objects.select_related('actividad__ponderacion')
            .values_list('alumno_id', 'actividad__ponderacion__materia_id')
            .distinct()
        )
        count = 0
        for alumno_id, materia_id in pairs:
            if materia_id is None:
                continue
            _, created = AlumnoMateriaProjection.objects.get_or_create(
                alumno_id=alumno_id,
                materia_id=materia_id,
                defaults={
                    'matricula': str(alumno_id),
                    'nombre': f'Alumno {alumno_id}',
                    'activa': True,
                },
            )
            if created:
                count += 1
        return count
