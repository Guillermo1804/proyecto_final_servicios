import os
from concurrent import futures
from unittest.mock import patch

import grpc
from django.test import TestCase, override_settings

from apps.notificaciones.services.data_provider import PlaceholderDataProvider
from apps.notificaciones.services.email_service import EmailService
from grpc_server.servicer import NotificacionesServicer
from proto_generated import agm_common_pb2
import notificaciones_pb2
import notificaciones_pb2_grpc


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
@patch.dict(
    os.environ,
    {'USE_PLACEHOLDER_DATA': 'True'},
    clear=False,
)
class NotificacionesGrpcServicerTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
        email = EmailService(data_provider=PlaceholderDataProvider())
        notificaciones_pb2_grpc.add_NotificacionesServiceServicer_to_server(
            NotificacionesServicer(email_service=email),
            cls._grpc_server,
        )
        cls._port = cls._grpc_server.add_insecure_port('[::]:0')
        cls._grpc_server.start()
        cls._channel = grpc.insecure_channel(f'localhost:{cls._port}')
        cls.stub = notificaciones_pb2_grpc.NotificacionesServiceStub(cls._channel)

    @classmethod
    def tearDownClass(cls):
        cls._channel.close()
        cls._grpc_server.stop(0)
        super().tearDownClass()

    def test_send_bienvenida_ok(self):
        response = self.stub.SendBienvenida(
            notificaciones_pb2.SendBienvenidaRequest(
                alumno_id=1,
                materia_id=10,
                clave_acceso='Clave123',
            )
        )
        self.assertTrue(response.success)
        self.assertIn('enviado', response.message.lower())

    def test_send_bienvenida_invalid_argument(self):
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.SendBienvenida(
                notificaciones_pb2.SendBienvenidaRequest(
                    alumno_id=1,
                    materia_id=10,
                    clave_acceso='',
                )
            )
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)

    def test_send_baja_ok(self):
        response = self.stub.SendBajaNotif(
            notificaciones_pb2.SendBajaRequest(
                alumno_id=1,
                docente_id=2,
                materia_id=3,
            )
        )
        self.assertTrue(response.success)

    def test_send_cierre_materia_ok(self):
        response = self.stub.SendCierreMateria(
            notificaciones_pb2.SendCierreMateriaRequest(materia_id=5)
        )
        self.assertTrue(response.success)
        self.assertIn('Enviados', response.message)

    def test_send_reset_password_ok(self):
        response = self.stub.SendResetPassword(
            notificaciones_pb2.SendResetPasswordRequest(
                delivery=agm_common_pb2.PasswordResetDelivery(
                    email='user@test.local',
                    reset_url='http://localhost:4200/reset?token=abc',
                ),
            )
        )
        self.assertTrue(response.success)

    def test_send_cierre_materia_not_found(self):
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.SendCierreMateria(
                notificaciones_pb2.SendCierreMateriaRequest(materia_id=-1)
            )
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)
