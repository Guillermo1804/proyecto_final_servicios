from decimal import Decimal

from django.test import TestCase

from apps.reportes.exceptions import MateriaNotFound
from apps.reportes.models import (
    ReporteAlumnoProjection,
    ReporteCalificacionProjection,
    ReporteMateriaProjection,
)
from apps.reportes.services.report_data_service import ReportDataService


class ReportDataServiceCalificacionesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ReporteMateriaProjection.objects.create(
            materia_id=1,
            periodo_id=2,
            periodo_nombre='2026-1',
            nrc='12345',
            nombre='Servicios Web',
            seccion='001',
            clave='COMP-456',
            docente_id=10,
            docente_nombre='Dr. Pérez',
            horario='Lun-Mie 10-12',
        )
        ReporteAlumnoProjection.objects.create(
            alumno_id=1,
            materia_id=1,
            matricula='20240001',
            nombre='Ana García López',
            activa=True,
            promedio_real=Decimal('7.65'),
            promedio_redondeado=8,
            presentes=9,
            retardos=1,
            ausentes=0,
            porcentaje_asistencia=Decimal('90.00'),
        )
        ReporteAlumnoProjection.objects.create(
            alumno_id=2,
            materia_id=1,
            matricula='20240002',
            nombre='Luis Martínez',
            activa=True,
            promedio_real=Decimal('5.45'),
            promedio_redondeado=5,
            presentes=7,
            retardos=0,
            ausentes=3,
            porcentaje_asistencia=Decimal('70.00'),
        )
        ReporteCalificacionProjection.objects.create(
            actividad_id=1,
            alumno_id=1,
            materia_id=1,
            categoria='Exámenes',
            porcentaje_categoria=Decimal('40.00'),
            actividad_nombre='Parcial 1',
            calificacion=Decimal('8.00'),
        )
        ReporteCalificacionProjection.objects.create(
            actividad_id=2,
            alumno_id=1,
            materia_id=1,
            categoria='Exámenes',
            porcentaje_categoria=Decimal('40.00'),
            actividad_nombre='Parcial 2',
            calificacion=Decimal('7.30'),
        )
        ReporteCalificacionProjection.objects.create(
            actividad_id=1,
            alumno_id=2,
            materia_id=1,
            categoria='Exámenes',
            porcentaje_categoria=Decimal('40.00'),
            actividad_nombre='Parcial 1',
            calificacion=Decimal('5.00'),
        )

    def test_fetch_calificaciones_merge_y_promedios(self):
        dto = ReportDataService().fetch_calificaciones(1)

        self.assertEqual(dto.materia.nrc, '12345')
        self.assertEqual(len(dto.alumnos), 2)
        ana = dto.alumnos[0]
        self.assertEqual(ana.matricula, '20240001')
        self.assertEqual(ana.nombre, 'Ana García López')
        self.assertAlmostEqual(ana.promedio_real, 7.65)
        self.assertEqual(ana.promedio_redondeado, 8)
        self.assertEqual(len(ana.calificaciones), 2)
        luis = dto.alumnos[1]
        self.assertAlmostEqual(luis.promedio_real, 5.45)
        self.assertEqual(luis.promedio_redondeado, 5)

    def test_fetch_calificaciones_materia_inexistente(self):
        with self.assertRaises(MateriaNotFound):
            ReportDataService().fetch_calificaciones(999)


class ReportDataServiceAsistenciasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ReporteMateriaProjection.objects.create(
            materia_id=1,
            periodo_id=2,
            periodo_nombre='2026-1',
            nrc='12345',
            nombre='Servicios Web',
            total_sesiones_qr=10,
            porcentaje_asistencia_grupal=Decimal('80.00'),
        )
        ReporteAlumnoProjection.objects.create(
            alumno_id=1,
            materia_id=1,
            matricula='20240001',
            nombre='Ana García López',
            activa=True,
            presentes=9,
            retardos=1,
            ausentes=0,
            porcentaje_asistencia=Decimal('90.00'),
        )
        ReporteAlumnoProjection.objects.create(
            alumno_id=2,
            materia_id=1,
            matricula='20240002',
            nombre='Luis Martínez',
            activa=True,
            presentes=0,
            retardos=0,
            ausentes=10,
            porcentaje_asistencia=Decimal('0.00'),
        )

    def test_fetch_asistencias_merge_completo(self):
        dto = ReportDataService().fetch_asistencias(1)

        self.assertEqual(dto.total_sesiones, 10)
        self.assertEqual(len(dto.alumnos), 2)
        ana = next(a for a in dto.alumnos if a.alumno_id == 1)
        self.assertEqual(ana.presentes, 9)
        self.assertEqual(ana.retardos, 1)
        self.assertEqual(ana.matricula, '20240001')

    def test_fetch_asistencias_incluye_inscritos_sin_registro_previo(self):
        ReporteAlumnoProjection.objects.filter(alumno_id=1).update(
            presentes=0,
            retardos=0,
            ausentes=10,
            porcentaje_asistencia=Decimal('0.00'),
        )

        dto = ReportDataService().fetch_asistencias(1)

        self.assertEqual(len(dto.alumnos), 2)
        for fila in dto.alumnos:
            self.assertEqual(fila.ausentes, 10)
            self.assertEqual(fila.presentes, 0)
