from django.test import SimpleTestCase, RequestFactory
from unittest.mock import MagicMock, patch

from apps.reportes.dto.report_dto import (
    AlumnoCalificacionRowDTO,
    CalificacionesReportDTO,
    MateriaEncabezadoDTO,
)
from apps.reportes.views import reportes_views
from apps.reportes.exceptions import MateriaNotFound
from io import BytesIO


def _calif_dto(docente_id: int = 10) -> CalificacionesReportDTO:
    return CalificacionesReportDTO(
        materia=MateriaEncabezadoDTO(
            materia_id=1,
            nrc='12345',
            nombre='Servicios Web',
            seccion='001',
            clave='COMP-456',
            docente_nombre='Dr. Pérez',
            docente_id=docente_id,
            periodo_id=2,
            periodo_nombre='2026-1',
            horario='Lun',
        ),
        categorias=(),
        alumnos=(
            AlumnoCalificacionRowDTO(
                alumno_id=1,
                matricula='20240001',
                nombre='Ana',
                calificaciones=(),
                promedio_real=8.0,
                promedio_redondeado=8,
            ),
        ),
    )


class ReportesViewsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('apps.reportes.views.reportes_views.build_report_bytes')
    @patch('apps.reportes.views.reportes_views.ReportDataService')
    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_calificaciones_xlsx_docente_titular(
        self, mock_auth, mock_service, mock_build
    ):
        mock_auth.return_value = MagicMock(user_id=10, rol='docente', email='d@test.local')
        mock_service.return_value.fetch_calificaciones.return_value = _calif_dto(10)
        mock_build.return_value = (b'fake-xlsx', 'calificaciones_12345.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        request = self.factory.get(
            '/reportes/calificaciones/1?formato=xlsx',
            HTTP_AUTHORIZATION='Bearer token',
        )
        response = reportes_views.reporte_calificaciones(request, materia_id=1)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'spreadsheetml',
            response['Content-Type'],
        )
        self.assertIn('calificaciones_12345.xlsx', response['Content-Disposition'])

    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_calificaciones_403_docente_no_titular(self, mock_auth):
        mock_auth.return_value = MagicMock(user_id=99, rol='docente', email='d@test.local')
        with patch('apps.reportes.views.reportes_views.ReportDataService') as mock_service:
            mock_service.return_value.fetch_calificaciones.return_value = _calif_dto(10)
            request = self.factory.get(
                '/reportes/calificaciones/1',
                HTTP_AUTHORIZATION='Bearer token',
            )
            response = reportes_views.reporte_calificaciones(request, materia_id=1)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data['success'])

    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_formato_invalido_400(self, mock_auth):
        mock_auth.return_value = MagicMock(user_id=10, rol='admin', email='a@test.local')
        request = self.factory.get(
            '/reportes/calificaciones/1?formato=doc',
            HTTP_AUTHORIZATION='Bearer token',
        )
        response = reportes_views.reporte_calificaciones(request, materia_id=1)
        self.assertEqual(response.status_code, 400)

    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_materia_no_encontrada_404(self, mock_auth):
        mock_auth.return_value = MagicMock(user_id=10, rol='admin', email='a@test.local')
        with patch('apps.reportes.views.reportes_views.ReportDataService') as mock_service:
            mock_service.return_value.fetch_calificaciones.side_effect = MateriaNotFound(999)
            request = self.factory.get(
                '/reportes/calificaciones/999',
                HTTP_AUTHORIZATION='Bearer token',
            )
            response = reportes_views.reporte_calificaciones(request, materia_id=999)

        self.assertEqual(response.status_code, 404)

    @patch('apps.reportes.views.reportes_views.build_report_bytes')
    @patch('apps.reportes.views.reportes_views.ReportDataService')
    @patch('apps.reportes.views.reportes_views.validate_token')
    def test_xls_alias_a_xlsx(self, mock_auth, mock_service, mock_build):
        mock_auth.return_value = MagicMock(user_id=10, rol='admin', email='a@test.local')
        mock_service.return_value.fetch_calificaciones.return_value = _calif_dto(10)
        mock_build.return_value = (b'fake', 'calificaciones_12345.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        request = self.factory.get(
            '/reportes/calificaciones/1?formato=xls',
            HTTP_AUTHORIZATION='Bearer token',
        )
        response = reportes_views.reporte_calificaciones(request, materia_id=1)

        self.assertEqual(response.status_code, 200)
        mock_build.assert_called_once()
