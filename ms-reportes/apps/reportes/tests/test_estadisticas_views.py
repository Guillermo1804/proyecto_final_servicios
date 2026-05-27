from django.test import RequestFactory, TestCase
from unittest.mock import MagicMock, patch

from apps.reportes.dto.report_dto import (
    AlumnoStatsDTO,
    MateriaAlumnoStatsDTO,
    StatsPeriodoDTO,
)
from apps.reportes.models import ReporteAlumnoProjection
from apps.reportes.views import estadisticas_views


def _periodo() -> StatsPeriodoDTO:
    return StatsPeriodoDTO(
        periodo_nombre='2026-1',
        periodo_id=2,
        materia_nombre='Servicios Web',
        materia_id=1,
        total_alumnos=25,
        aprobados=20,
        reprobados=5,
        promedio_grupal=7.8,
        porcentaje_asistencia=82.5,
    )


class EstadisticasViewsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('apps.reportes.views.estadisticas_views.EstadisticasService')
    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_docente_self_ok(self, mock_auth, mock_service):
        mock_auth.return_value = MagicMock(user_id=10, rol='docente', email='d@test.local')
        mock_service.return_value.historial_docente.return_value = (_periodo(),)

        request = self.factory.get(
            '/estadisticas/docente/10',
            HTTP_AUTHORIZATION='Bearer t',
        )
        response = estadisticas_views.estadisticas_docente(request, usuario_id=10)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['docente_id'], 10)
        self.assertEqual(len(response.data['data']['periodos']), 1)
        self.assertEqual(response.data['data']['periodos'][0]['aprobados'], 20)
        self.assertEqual(len(response.data['data']['comparativa']), 1)

    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_docente_otro_id_403(self, mock_auth):
        mock_auth.return_value = MagicMock(user_id=10, rol='docente', email='d@test.local')
        request = self.factory.get(
            '/estadisticas/docente/99',
            HTTP_AUTHORIZATION='Bearer t',
        )
        response = estadisticas_views.estadisticas_docente(request, usuario_id=99)
        self.assertEqual(response.status_code, 403)

    @patch('apps.reportes.views.estadisticas_views.EstadisticasService')
    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_alumno_admin_ok(self, mock_auth, mock_service):
        mock_auth.return_value = MagicMock(user_id=1, rol='admin', email='a@test.local')
        mock_service.return_value.stats_alumno.return_value = AlumnoStatsDTO(
            alumno_id=5,
            matricula='20240001',
            nombre='Ana',
            email='ana@test.local',
            materias=(
                MateriaAlumnoStatsDTO(
                    materia_id=1,
                    materia_nombre='SW',
                    periodo_nombre='2026-1',
                    promedio_real=8.0,
                    promedio_redondeado=8,
                    total_sesiones=10,
                    presentes=9,
                    retardos=1,
                    ausentes=0,
                    porcentaje_asistencia=90.0,
                ),
            ),
        )

        request = self.factory.get(
            '/estadisticas/alumno/5',
            HTTP_AUTHORIZATION='Bearer t',
        )
        response = estadisticas_views.estadisticas_alumno(request, alumno_id=5)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['alumno_id'], 5)
        self.assertAlmostEqual(response.data['data']['materias'][0]['promedio_real'], 8.0)

    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_alumno_id_ajeno_403(self, mock_auth):
        mock_auth.return_value = MagicMock(user_id=100, rol='alumno', email='a@test.local')
        ReporteAlumnoProjection.objects.create(
            alumno_id=5,
            materia_id=1,
            usuario_id=999,
            matricula='20240001',
            nombre='Ana',
            email='ana@test.local',
            activa=True,
        )

        request = self.factory.get(
            '/estadisticas/alumno/5',
            HTTP_AUTHORIZATION='Bearer t',
        )
        response = estadisticas_views.estadisticas_alumno(request, alumno_id=5)
        self.assertEqual(response.status_code, 403)

    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_alumno_self_passes_check(self, mock_auth):
        mock_auth.return_value = MagicMock(user_id=100, rol='alumno', email='a@test.local')
        ReporteAlumnoProjection.objects.create(
            alumno_id=5,
            materia_id=1,
            usuario_id=100,
            matricula='20240001',
            nombre='Ana',
            email='ana@test.local',
            activa=True,
        )

        with patch('apps.reportes.views.estadisticas_views.EstadisticasService') as mock_svc:
            mock_svc.return_value.stats_alumno.return_value = AlumnoStatsDTO(
                alumno_id=5,
                matricula='1',
                nombre='Ana',
                email='a@t.local',
                materias=(),
            )
            request = self.factory.get(
                '/estadisticas/alumno/5',
                HTTP_AUTHORIZATION='Bearer t',
            )
            response = estadisticas_views.estadisticas_alumno(request, alumno_id=5)

        self.assertEqual(response.status_code, 200)

    @patch('apps.reportes.views.estadisticas_views.EstadisticasService')
    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_docente_paginacion(self, mock_auth, mock_service):
        mock_auth.return_value = MagicMock(user_id=1, rol='admin', email='a@test.local')
        mock_service.return_value.historial_docente.return_value = tuple(
            _periodo() for _ in range(5)
        )

        request = self.factory.get(
            '/estadisticas/docente/1?page=1&limit=2',
            HTTP_AUTHORIZATION='Bearer t',
        )
        response = estadisticas_views.estadisticas_docente(request, usuario_id=1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']['periodos']), 2)
        self.assertEqual(response.data['pagination']['total'], 5)
