"""Carga inicial de proyecciones MS-5."""

from __future__ import annotations

import MySQLdb
from decouple import config
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.event_bus import projection_service as proj
from apps.core.models import AlumnoProjection, MateriaProjection, PeriodoProjection


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
    help = 'Backfill de PeriodoProjection, MateriaProjection y AlumnoProjection'

    def add_arguments(self, parser):
        parser.add_argument('--from-local-only', action='store_true')

    def handle(self, *args, **options):
        periodos = materias = alumnos = 0
        if not options['from_local_only']:
            periodos = self._backfill_periodos()
            materias = self._backfill_materias()
            alumnos = self._backfill_alumnos()
        self.stdout.write(
            self.style.SUCCESS(
                f'Backfill: periodos={periodos}, materias={materias}, alumnos={alumnos}'
            )
        )

    def _backfill_periodos(self) -> int:
        conn = _mysql_conn('BACKFILL_PERIODOS_DB')
        if conn is None:
            self.stdout.write('BACKFILL_PERIODOS_DB_* omitido')
            return 0
        count = 0
        try:
            cur = conn.cursor()
            cur.execute('SELECT id, nombre, activo FROM periodos')
            for row in cur.fetchall():
                proj.upsert_periodo({'periodo_id': row[0], 'nombre': row[1], 'activo': bool(row[2])})
                count += 1
        finally:
            conn.close()
        return count

    def _backfill_materias(self) -> int:
        conn = _mysql_conn('BACKFILL_PERIODOS_DB')
        if conn is None:
            return 0
        count = 0
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT m.id, m.periodo_id, m.nrc, m.nombre, m.docente_id, p.activo
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
                        'docente_id': row[4],
                    },
                    periodo_activo=bool(row[5]),
                )
                count += 1
        finally:
            conn.close()
        return count

    def _backfill_alumnos(self) -> int:
        conn = _mysql_conn('BACKFILL_ALUMNOS_DB')
        if conn is None:
            self.stdout.write('BACKFILL_ALUMNOS_DB_* omitido')
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
