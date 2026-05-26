"""Trunca proyecciones analíticas y las reconstruye (demo o backfill opcional)."""

from __future__ import annotations

import logging
import unicodedata
from decimal import Decimal

import MySQLdb
from decouple import config
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.reportes.event_bus import projection_service as proj
from apps.reportes.models import (
    EventInbox,
    ReportAnalyticsState,
    ReporteAlumnoProjection,
    ReporteAsistenciaProjection,
    ReporteCalificacionProjection,
    ReporteMateriaProjection,
    ReportePeriodoProjection,
)
from apps.reportes.services.analytics_state import reset_analytics_state, touch_data_as_of

logger = logging.getLogger(__name__)


def _normalize_docente_text(value: str) -> str:
    text = unicodedata.normalize('NFD', value or '')
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    return text.lower().strip()


def _docente_nombre_matches(en_materia: str, nombre: str, apellido: str) -> bool:
    """Misma heurística que el frontend (tokens en docente_nombre del PDF)."""
    en_materia_n = _normalize_docente_text(en_materia)
    if not en_materia_n:
        return False
    tokens = [
        token
        for token in _normalize_docente_text(f'{nombre} {apellido}').split()
        if len(token) >= 2
    ]
    if not tokens:
        return False
    coincidencias = sum(1 for token in tokens if token in en_materia_n)
    minimo = len(tokens) if len(tokens) <= 2 else 2
    return coincidencias >= minimo


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
    help = 'Trunca proyecciones MS-7 y reconstruye estado analítico (demo o BACKFILL_* DB)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--demo-seed',
            action='store_true',
            help='Carga dataset histórico de prueba en db-reportes (sin MS-2…MS-5)',
        )
        parser.add_argument(
            '--from-backfill',
            action='store_true',
            help='Intenta leer BACKFILL_PERIODOS_DB_* y BACKFILL_ALUMNOS_DB_* si están definidos',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            self._truncate_all()
            reset_analytics_state()

        if options['from_backfill']:
            self._backfill_from_databases()

        if options['demo_seed'] or not options['from_backfill']:
            self._seed_demo_dataset()

        touch_data_as_of()
        self.stdout.write(self.style.SUCCESS('rebuild_report_projections completado'))

    def _truncate_all(self) -> None:
        EventInbox.objects.all().delete()
        ReporteAsistenciaProjection.objects.all().delete()
        ReporteCalificacionProjection.objects.all().delete()
        ReporteAlumnoProjection.objects.all().delete()
        ReporteMateriaProjection.objects.all().delete()
        ReportePeriodoProjection.objects.all().delete()
        self.stdout.write('Proyecciones e inbox truncados')

    def _seed_demo_dataset(self) -> None:
        """Dataset mínimo para pruebas Fase 8 (materia_id=1, docente_id=1)."""
        now = timezone.now()
        proj.upsert_periodo({'periodo_id': 1, 'nombre': '2025-1 Otoño', 'activo': True})
        proj.upsert_materia(
            {
                'materia_id': 1,
                'periodo_id': 1,
                'periodo_nombre': '2025-1 Otoño',
                'nrc': '12345',
                'nombre': 'Programación Avanzada',
                'seccion': '01',
                'clave': 'CC305',
                'docente_id': 1,
                'docente_nombre': 'Dr. Demo',
                'horario': 'Lun-Mie 10:00',
            }
        )
        proj.handle_alumno_imported(
            {
                'alumno_id': 1,
                'materia_id': 1,
                'periodo_id': 1,
                'matricula': '2021001',
                'nombre': 'Ana Pérez',
                'email': 'ana@buap.mx',
                'materia_nombre': 'Programación Avanzada',
                'nrc': '12345',
            }
        )
        proj.handle_alumno_imported(
            {
                'alumno_id': 2,
                'materia_id': 1,
                'periodo_id': 1,
                'matricula': '2021002',
                'nombre': 'Luis García',
                'email': 'luis@buap.mx',
                'materia_nombre': 'Programación Avanzada',
                'nrc': '12345',
            }
        )
        ReporteAlumnoProjection.objects.filter(alumno_id=1).update(usuario_id=3)
        ReporteAlumnoProjection.objects.filter(alumno_id=2).update(usuario_id=4)

        proj.handle_actividad_created(
            {
                'actividad_id': 101,
                'materia_id': 1,
                'ponderacion_id': 1,
                'nombre': 'Parcial 1',
                'categoria': 'Exámenes',
            }
        )
        proj.handle_actividad_created(
            {
                'actividad_id': 102,
                'materia_id': 1,
                'ponderacion_id': 2,
                'nombre': 'Tarea 1',
                'categoria': 'Tareas',
            }
        )
        ReporteCalificacionProjection.objects.filter(actividad_id=101).update(
            porcentaje_categoria=Decimal('60'),
        )
        ReporteCalificacionProjection.objects.filter(actividad_id=102).update(
            porcentaje_categoria=Decimal('40'),
        )

        proj.handle_calificacion_updated(
            {
                'calificacion_id': 1,
                'actividad_id': 101,
                'alumno_id': 1,
                'materia_id': 1,
                'calificacion': 8.5,
            }
        )
        proj.handle_calificacion_updated(
            {
                'calificacion_id': 2,
                'actividad_id': 102,
                'alumno_id': 1,
                'materia_id': 1,
                'calificacion': 9.0,
            }
        )
        proj.handle_calificacion_updated(
            {
                'calificacion_id': 3,
                'actividad_id': 101,
                'alumno_id': 2,
                'materia_id': 1,
                'calificacion': 5.0,
            }
        )
        proj.handle_calificacion_updated(
            {
                'calificacion_id': 4,
                'actividad_id': 102,
                'alumno_id': 2,
                'materia_id': 1,
                'calificacion': 6.0,
            }
        )
        proj.handle_concentrado_calculado(
            {
                'materia_id': 1,
                'total_alumnos': 2,
                'promedio_grupal': 7.1,
                'nrc': '12345',
                'materia_nombre': 'Programación Avanzada',
            }
        )

        for _ in range(3):
            proj.handle_qr_session_created({'materia_id': 1, 'sesion_id': 10 + _})

        proj.handle_asistencia_registered(
            {
                'sesion_id': 10,
                'materia_id': 1,
                'alumno_id': 1,
                'estado': 'presente',
                'minuto_registro': 2,
            }
        )
        proj.handle_asistencia_registered(
            {
                'sesion_id': 11,
                'materia_id': 1,
                'alumno_id': 1,
                'estado': 'retardo',
                'minuto_registro': 7,
            }
        )
        proj.handle_asistencia_registered(
            {
                'sesion_id': 10,
                'materia_id': 1,
                'alumno_id': 2,
                'estado': 'presente',
                'minuto_registro': 1,
            }
        )

        touch_data_as_of(now)
        self.stdout.write(self.style.SUCCESS('Dataset demo cargado (materia_id=1)'))

    def _backfill_from_databases(self) -> None:
        count = 0
        conn = _mysql_conn('BACKFILL_PERIODOS_DB')
        if conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT m.id, m.periodo_id, m.nrc, m.nombre, m.seccion, m.clave,
                       m.docente_nombre, m.docente_id, m.horario, p.nombre
                FROM materias m
                JOIN periodos p ON p.id = m.periodo_id
                """
            )
            for row in cur.fetchall():
                proj.upsert_periodo({'periodo_id': row[1], 'nombre': row[9], 'activo': True})
                proj.upsert_materia(
                    {
                        'materia_id': row[0],
                        'periodo_id': row[1],
                        'nrc': row[2] or '',
                        'nombre': row[3] or '',
                        'seccion': row[4] or '',
                        'clave': row[5] or '',
                        'docente_nombre': row[6] or '',
                        'docente_id': row[7],
                        'horario': row[8] or '',
                        'periodo_nombre': row[9] or '',
                    }
                )
                count += 1
            conn.close()
            self.stdout.write(f'Backfill periodos/materias: {count}')
        else:
            self.stdout.write('BACKFILL_PERIODOS_DB_* no configurado')

        ins = 0
        conn = _mysql_conn('BACKFILL_ALUMNOS_DB')
        if conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT a.id, a.matricula,
                       TRIM(CONCAT(a.nombre, ' ', a.apellido)),
                       a.email, am.materia_id, a.usuario_id
                FROM core_alumno a
                JOIN core_inscripcionmateria am ON am.alumno_id = a.id
                WHERE am.activa = 1
                """
            )
            for row in cur.fetchall():
                proj.upsert_alumno_materia(
                    alumno_id=row[0],
                    materia_id=row[4],
                    matricula=row[1] or '',
                    nombre=row[2] or '',
                    email=row[3] or '',
                    usuario_id=row[5],
                    activa=True,
                )
                ins += 1
            conn.close()
            self.stdout.write(f'Backfill inscripciones: {ins}')
            self._resolve_docente_usuario_ids()
        else:
            self.stdout.write('BACKFILL_ALUMNOS_DB_* no configurado')

    def _resolve_docente_usuario_ids(self) -> None:
        """Asigna docente_id=usuario_id (MS-1) cuando periodos solo trae docente_nombre."""
        conn = _mysql_conn('BACKFILL_ALUMNOS_DB')
        if not conn:
            return

        cur = conn.cursor()
        cur.execute(
            'SELECT usuario_id, nombre, apellido FROM core_docente WHERE usuario_id IS NOT NULL'
        )
        docentes = cur.fetchall()
        conn.close()

        linked = 0
        for materia in ReporteMateriaProjection.objects.filter(docente_id__isnull=True):
            for usuario_id, nombre, apellido in docentes:
                if _docente_nombre_matches(materia.docente_nombre, nombre or '', apellido or ''):
                    ReporteMateriaProjection.objects.filter(materia_id=materia.materia_id).update(
                        docente_id=usuario_id,
                    )
                    linked += 1
                    break

        self.stdout.write(f'Docente usuario_id vinculados: {linked}')
