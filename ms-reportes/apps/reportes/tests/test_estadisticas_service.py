from decimal import Decimal

from django.test import TestCase

from apps.reportes.exceptions import AlumnoNotFound
from apps.reportes.models import ReporteAlumnoProjection, ReporteMateriaProjection
from apps.reportes.services.estadisticas_service import EstadisticasService


class EstadisticasServiceDocenteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ReporteMateriaProjection.objects.create(
            materia_id=1,
            periodo_id=2,
            periodo_nombre='2026-1',
            nrc='12345',
            nombre='Servicios Web',
            docente_id=10,
            total_alumnos=25,
            aprobados=20,
            reprobados=5,
            promedio_grupal=Decimal('7.80'),
            porcentaje_asistencia_grupal=Decimal('82.50'),
        )

    def test_historial_docente_desde_proyeccion_local(self):
        periodos = EstadisticasService().historial_docente(10)

        self.assertEqual(len(periodos), 1)
        row = periodos[0]
        self.assertEqual(row.aprobados, 20)
        self.assertEqual(row.reprobados, 5)
        self.assertAlmostEqual(row.promedio_grupal, 7.8)
        self.assertAlmostEqual(row.porcentaje_asistencia, 82.5)


class EstadisticasServiceAlumnoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ReporteMateriaProjection.objects.create(
            materia_id=1,
            periodo_id=2,
            periodo_nombre='2026-1',
            nrc='12345',
            nombre='Servicios Web',
            total_sesiones_qr=10,
        )
        ReporteAlumnoProjection.objects.create(
            alumno_id=1,
            materia_id=1,
            matricula='20240001',
            nombre='Ana García',
            email='ana@test.local',
            activa=True,
            promedio_real=Decimal('7.65'),
            promedio_redondeado=8,
            presentes=9,
            retardos=1,
            ausentes=0,
            porcentaje_asistencia=Decimal('90.00'),
        )

    def test_stats_alumno_desde_proyeccion_local(self):
        stats = EstadisticasService().stats_alumno(1)

        self.assertEqual(stats.alumno_id, 1)
        self.assertEqual(len(stats.materias), 1)
        materia = stats.materias[0]
        self.assertAlmostEqual(materia.promedio_real, 7.65)
        self.assertEqual(materia.promedio_redondeado, 8)
        self.assertEqual(materia.presentes, 9)

    def test_stats_alumno_inexistente(self):
        with self.assertRaises(AlumnoNotFound):
            EstadisticasService().stats_alumno(999)
