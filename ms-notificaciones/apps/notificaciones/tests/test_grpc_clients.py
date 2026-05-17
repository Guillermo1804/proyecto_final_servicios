import grpc
from django.test import SimpleTestCase
from unittest.mock import MagicMock, patch

from apps.notificaciones.exceptions import AlumnoNotFound, MateriaNotFound, UpstreamUnavailable
from grpc_clients.errors import map_rpc_error


class MapRpcErrorTests(SimpleTestCase):
    def test_not_found_alumno(self):
        exc = grpc.RpcError()
        exc.code = lambda: grpc.StatusCode.NOT_FOUND
        exc.details = lambda: 'no existe'
        with self.assertRaises(AlumnoNotFound):
            map_rpc_error(exc, 'ms-alumnos', entity='alumno', entity_id=42)

    def test_not_found_materia(self):
        exc = grpc.RpcError()
        exc.code = lambda: grpc.StatusCode.NOT_FOUND
        exc.details = lambda: ''
        with self.assertRaises(MateriaNotFound):
            map_rpc_error(exc, 'ms-periodos', entity='materia', entity_id=10)

    def test_deadline_exceeded(self):
        exc = grpc.RpcError()
        exc.code = lambda: grpc.StatusCode.DEADLINE_EXCEEDED
        exc.details = lambda: ''
        with self.assertRaises(UpstreamUnavailable):
            map_rpc_error(exc, 'ms-alumnos', entity='alumno', entity_id=1)


class GrpcDataProviderTests(SimpleTestCase):
    @patch('apps.notificaciones.services.data_provider.alumnos_client.get_alumno_by_id')
    def test_grpc_provider_maps_alumno(self, mock_get):
        from proto_generated import alumnos_pb2
        from apps.notificaciones.services.data_provider import GrpcDataProvider

        mock_get.return_value = alumnos_pb2.AlumnoInfo(
            id=1,
            usuario_id=10,
            matricula='20240001',
            nombre='Ana Test',
            email='ana@test.local',
            tipo_formacion='ISC',
        )
        alumno = GrpcDataProvider().get_alumno(1)
        self.assertEqual(alumno.email, 'ana@test.local')
        mock_get.assert_called_once_with(1)
