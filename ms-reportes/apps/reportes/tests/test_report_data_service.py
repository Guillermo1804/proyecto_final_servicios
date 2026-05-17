from django.test import SimpleTestCase
from unittest.mock import patch

from apps.reportes.services.report_data_service import ReportDataService
from grpc_clients.mocks import mock_concentrado, mock_estadisticas_asistencia
from proto_generated import alumnos_pb2, periodos_pb2


def _materia_proto(materia_id: int = 1) -> periodos_pb2.MateriaInfo:
    return periodos_pb2.MateriaInfo(
        id=materia_id,
        nrc='12345',
        nombre='Servicios Web',
        seccion='001',
        clave='COMP-456',
        docente_nombre='Dr. Pérez',
        docente_id=10,
        horario='Lun-Mie 10-12',
        periodo_id=2,
        periodo_nombre='2026-1',
    )


def _alumnos_list() -> alumnos_pb2.AlumnosListResponse:
    return alumnos_pb2.AlumnosListResponse(
        alumnos=[
            alumnos_pb2.AlumnoInfo(
                id=1,
                usuario_id=101,
                matricula='20240001',
                nombre='Ana García López',
                email='ana@test.local',
                tipo_formacion='ISC',
            ),
            alumnos_pb2.AlumnoInfo(
                id=2,
                usuario_id=102,
                matricula='20240002',
                nombre='Luis Martínez',
                email='luis@test.local',
                tipo_formacion='ISC',
            ),
        ]
    )


class ReportDataServiceCalificacionesTests(SimpleTestCase):
    @patch('apps.reportes.services.report_data_service.alumnos_client.get_alumnos_by_materia')
    @patch('apps.reportes.services.report_data_service.calificaciones_client.get_concentrado')
    @patch('apps.reportes.services.report_data_service.periodos_client.get_materia_by_id')
    def test_fetch_calificaciones_merge_y_promedios_ms4(
        self, mock_materia, mock_concentrado_fn, mock_alumnos
    ):
        mock_materia.return_value = _materia_proto()
        concentrado = mock_concentrado(1)
        concentrado.alumnos[0].matricula = ''
        concentrado.alumnos[0].nombre = ''
        mock_concentrado_fn.return_value = concentrado
        mock_alumnos.return_value = _alumnos_list()

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

    @patch('apps.reportes.services.report_data_service.alumnos_client.get_alumnos_by_materia')
    @patch('apps.reportes.services.report_data_service.calificaciones_client.get_concentrado')
    @patch('apps.reportes.services.report_data_service.periodos_client.get_materia_by_id')
    def test_fetch_calificaciones_respeta_nombre_ms4_si_existe(
        self, mock_materia, mock_concentrado_fn, mock_alumnos
    ):
        mock_materia.return_value = _materia_proto()
        mock_concentrado_fn.return_value = mock_concentrado(1)
        mock_alumnos.return_value = alumnos_pb2.AlumnosListResponse()

        dto = ReportDataService().fetch_calificaciones(1)
        self.assertEqual(dto.alumnos[0].nombre, 'Ana García López')


class ReportDataServiceAsistenciasTests(SimpleTestCase):
    @patch('apps.reportes.services.report_data_service.alumnos_client.get_alumnos_by_materia')
    @patch('apps.reportes.services.report_data_service.asistencias_client.get_estadisticas_asistencia')
    @patch('apps.reportes.services.report_data_service.periodos_client.get_materia_by_id')
    def test_fetch_asistencias_merge_completo(
        self, mock_materia, mock_stats, mock_alumnos
    ):
        mock_materia.return_value = _materia_proto()
        mock_stats.return_value = mock_estadisticas_asistencia(1)
        mock_alumnos.return_value = _alumnos_list()

        dto = ReportDataService().fetch_asistencias(1)

        self.assertEqual(dto.total_sesiones, 10)
        self.assertEqual(len(dto.alumnos), 2)
        ana = next(a for a in dto.alumnos if a.alumno_id == 1)
        self.assertEqual(ana.presentes, 9)
        self.assertEqual(ana.retardos, 1)
        self.assertEqual(ana.matricula, '20240001')

    @patch('apps.reportes.services.report_data_service.alumnos_client.get_alumnos_by_materia')
    @patch('apps.reportes.services.report_data_service.asistencias_client.get_estadisticas_asistencia')
    @patch('apps.reportes.services.report_data_service.periodos_client.get_materia_by_id')
    def test_fetch_asistencias_inscrito_sin_registro_ms5(
        self, mock_materia, mock_stats, mock_alumnos
    ):
        mock_materia.return_value = _materia_proto()
        stats = mock_estadisticas_asistencia(1)
        del stats.alumnos[:]
        mock_stats.return_value = stats
        mock_alumnos.return_value = _alumnos_list()

        dto = ReportDataService().fetch_asistencias(1)

        self.assertEqual(len(dto.alumnos), 2)
        for fila in dto.alumnos:
            self.assertEqual(fila.ausentes, 10)
            self.assertEqual(fila.presentes, 0)
