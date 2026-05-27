import grpc
from django.test import SimpleTestCase
from unittest.mock import MagicMock, patch

from grpc_clients import asistencias_client, calificaciones_client, channel, periodos_client
from grpc_clients.exceptions import (
    AlumnoNotFound,
    MateriaNotFound,
    PermissionDenied,
    UpstreamUnavailable,
    map_rpc_error,
)


def _rpc_error(code: grpc.StatusCode, details: str = '') -> grpc.RpcError:
    exc = grpc.RpcError()
    exc.code = lambda: code
    exc.details = lambda: details
    return exc


class MapRpcErrorTests(SimpleTestCase):
    def test_not_found_materia(self):
        with self.assertRaises(MateriaNotFound):
            map_rpc_error(
                _rpc_error(grpc.StatusCode.NOT_FOUND),
                'ms-periodos',
                entity='materia',
                entity_id=10,
            )

    def test_not_found_alumno(self):
        with self.assertRaises(AlumnoNotFound):
            map_rpc_error(
                _rpc_error(grpc.StatusCode.NOT_FOUND),
                'ms-alumnos',
                entity='alumno',
                entity_id=42,
            )

    def test_unavailable(self):
        with self.assertRaises(UpstreamUnavailable):
            map_rpc_error(
                _rpc_error(grpc.StatusCode.UNAVAILABLE, 'down'),
                'ms-calificaciones',
                entity='materia',
                entity_id=1,
            )

    def test_permission_denied(self):
        with self.assertRaises(PermissionDenied):
            map_rpc_error(
                _rpc_error(grpc.StatusCode.PERMISSION_DENIED),
                'ms-calificaciones',
                entity='materia',
                entity_id=1,
            )


class ChannelTests(SimpleTestCase):
    def tearDown(self):
        channel.clear_channels()

    @patch('grpc_clients.channel.config')
    @patch('grpc.insecure_channel')
    def test_singleton_per_service(self, mock_channel, mock_config):
        mock_config.side_effect = lambda key, default=None: {
            'MS_AUTH_GRPC_HOST': 'ms-auth',
            'MS_AUTH_GRPC_PORT': '50051',
        }.get(key, default)
        ch1 = channel.get_channel('auth', 'MS_AUTH_GRPC_HOST', 'MS_AUTH_GRPC_PORT', 'ms-auth', '50051')
        ch2 = channel.get_channel('auth', 'MS_AUTH_GRPC_HOST', 'MS_AUTH_GRPC_PORT', 'ms-auth', '50051')
        self.assertIs(ch1, ch2)
        mock_channel.assert_called_once()


class MockClientTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._block_patchers = [
            patch('grpc_clients.calificaciones_client.block_business_grpc'),
            patch('grpc_clients.asistencias_client.block_business_grpc'),
            patch('grpc_clients.periodos_client.block_business_grpc'),
        ]
        for patcher in cls._block_patchers:
            patcher.start()

    @classmethod
    def tearDownClass(cls):
        for patcher in reversed(cls._block_patchers):
            patcher.stop()
        super().tearDownClass()

    @patch('grpc_clients.calificaciones_client.use_mock_data', return_value=True)
    def test_get_concentrado_mock(self, _mock_flag):
        resp = calificaciones_client.get_concentrado(99)
        self.assertEqual(resp.materia_id, 99)
        self.assertEqual(len(resp.alumnos), 2)
        self.assertAlmostEqual(resp.alumnos[0].promedio_real, 7.65)
        self.assertEqual(resp.alumnos[0].promedio_redondeado, 8)

    @patch('grpc_clients.asistencias_client.use_mock_data', return_value=True)
    def test_get_estadisticas_asistencia_mock(self, _mock_flag):
        resp = asistencias_client.get_estadisticas_asistencia(5)
        self.assertEqual(resp.materia_id, 5)
        self.assertEqual(resp.total_sesiones, 10)
        self.assertEqual(len(resp.alumnos), 2)

    @patch('grpc_clients.calificaciones_client.use_mock_data', return_value=False)
    @patch('grpc_clients.calificaciones_client.get_calificaciones_stub')
    def test_get_concentrado_fallback_on_unavailable(self, mock_stub_factory, _mock_flag):
        stub = MagicMock()
        stub.GetConcentrado.side_effect = _rpc_error(grpc.StatusCode.UNAVAILABLE)
        mock_stub_factory.return_value = stub
        resp = calificaciones_client.get_concentrado(1)
        self.assertEqual(resp.materia_id, 1)
        self.assertGreater(len(resp.alumnos), 0)

    @patch('grpc_clients.periodos_client.get_periodos_stub')
    def test_get_materia_by_id_not_found(self, mock_stub_factory):
        stub = MagicMock()
        stub.GetMateriaById.side_effect = _rpc_error(grpc.StatusCode.NOT_FOUND, 'no existe')
        mock_stub_factory.return_value = stub
        with self.assertRaises(MateriaNotFound):
            periodos_client.get_materia_by_id(999)
