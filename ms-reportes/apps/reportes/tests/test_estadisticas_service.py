from django.test import SimpleTestCase
from unittest.mock import patch

from apps.reportes.services.estadisticas_service import EstadisticasService
from grpc_clients.mocks import mock_concentrado
from proto_generated import alumnos_pb2, calificaciones_pb2, periodos_pb2


def _materia_list() -> periodos_pb2.MateriasListResponse:
    return periodos_pb2.MateriasListResponse(
        materias=[
            periodos_pb2.MateriaInfo(
                id=1,
                nrc='12345',
                nombre='Servicios Web',
                seccion='001',
                clave='COMP-456',
                docente_nombre='Dr. Pérez',
                docente_id=10,
                horario='Lun-Mie',
                periodo_id=2,
                periodo_nombre='2026-1',
            ),
        ]
    )


class EstadisticasServiceDocenteTests(SimpleTestCase):
    @patch('apps.reportes.services.estadisticas_service.asistencias_client.get_estadisticas_asistencia')
    @patch('apps.reportes.services.estadisticas_service.calificaciones_client.get_estadisticas_materia')
    @patch('apps.reportes.services.estadisticas_service.periodos_client.get_materias_by_docente')
    def test_historial_docente_usa_stats_ms4(
        self, mock_materias, mock_stats_cal, mock_stats_asi
    ):
        mock_materias.return_value = _materia_list()
        mock_stats_cal.return_value = calificaciones_pb2.EstadisticasMateriaResponse(
            total_alumnos=25,
            aprobados=20,
            reprobados=5,
            promedio_grupal=7.8,
            calificacion_maxima=10.0,
            calificacion_minima=5.0,
        )
        from grpc_clients.mocks import mock_estadisticas_asistencia

        mock_stats_asi.return_value = mock_estadisticas_asistencia(1)

        periodos = EstadisticasService().historial_docente(10)

        self.assertEqual(len(periodos), 1)
        row = periodos[0]
        self.assertEqual(row.aprobados, 20)
        self.assertEqual(row.reprobados, 5)
        self.assertAlmostEqual(row.promedio_grupal, 7.8)
        self.assertAlmostEqual(row.porcentaje_asistencia, 82.5)


class EstadisticasServiceAlumnoTests(SimpleTestCase):
    @patch('apps.reportes.services.estadisticas_service.asistencias_client.get_asistencia_alumno')
    @patch('apps.reportes.services.estadisticas_service.calificaciones_client.get_promedio_alumno')
    @patch('apps.reportes.services.estadisticas_service.periodos_client.get_materia_by_id')
    @patch('apps.reportes.services.estadisticas_service.alumnos_client.get_alumno_by_id')
    @patch('apps.reportes.services.estadisticas_service._materia_ids_para_alumno', return_value=[1])
    def test_stats_alumno_promedios_ms4(
        self, _mock_ids, mock_alumno, mock_materia, mock_promedio, mock_asistencia
    ):
        mock_alumno.return_value = alumnos_pb2.AlumnoInfo(
            id=1,
            usuario_id=101,
            matricula='20240001',
            nombre='Ana García',
            email='ana@test.local',
            tipo_formacion='ISC',
        )
        mock_materia.return_value = _materia_list().materias[0]
        concentrado = mock_concentrado(1)
        mock_promedio.return_value = calificaciones_pb2.PromedioResponse(
            promedio_real=concentrado.alumnos[0].promedio_real,
            promedio_redondeado=concentrado.alumnos[0].promedio_redondeado,
        )
        from grpc_clients.mocks import mock_asistencia_alumno

        mock_asistencia.return_value = mock_asistencia_alumno(1, 1)

        stats = EstadisticasService().stats_alumno(1)

        self.assertEqual(stats.alumno_id, 1)
        self.assertEqual(len(stats.materias), 1)
        materia = stats.materias[0]
        self.assertAlmostEqual(materia.promedio_real, 7.65)
        self.assertEqual(materia.promedio_redondeado, 8)
        self.assertEqual(materia.presentes, 9)
