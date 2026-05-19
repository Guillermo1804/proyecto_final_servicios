import os
import unittest
from unittest.mock import MagicMock, patch

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.services import create_user_account

User = get_user_model()

TEST_SECRET = 'test-secret-key-for-jwt-ms1-32bytes!!'
TEST_ENV = {
    'SECRET_KEY': TEST_SECRET,
}
def _jwt_override():
    return {
        'SECRET_KEY': TEST_SECRET,
        'SIMPLE_JWT': {
            **django_settings.SIMPLE_JWT,
            'SIGNING_KEY': TEST_SECRET,
        },
    }

try:
    from apps.core.grpc_servicer import AuthServiceServicer
    from proto_generated import auth_pb2

    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    AuthServiceServicer = None
    auth_pb2 = None


@unittest.skipUnless(GRPC_AVAILABLE, 'proto_generated no disponible en este entorno')
@patch.dict(os.environ, TEST_ENV, clear=False)
class AuthGrpcServicerTests(TestCase):
    """Pruebas del servicer sin levantar puerto (T8, T9)."""

    @classmethod
    def setUpClass(cls):
        cls._settings = override_settings(**_jwt_override())
        cls._settings.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._settings.disable()

    def setUp(self):
        self.servicer = AuthServiceServicer()
        self.context = MagicMock()
        self.user = User.objects.create_user(
            email='grpc@test.local',
            nombre='GRPC User',
            rol='docente',
            password='GrpcPass123!',
        )

    def _access_token_via_login(self):
        client = APIClient()
        response = client.post(
            '/auth/login',
            {'email': 'grpc@test.local', 'password': 'GrpcPass123!'},
            format='json',
        )
        return response.json()['data']['access_token']

    def test_t8_validate_token_invalid(self):
        req = auth_pb2.ValidateTokenRequest(token='invalid')
        response = self.servicer.ValidateToken(req, self.context)
        self.assertFalse(response.valid)

    def test_validate_token_valid(self):
        token = self._access_token_via_login()
        req = auth_pb2.ValidateTokenRequest(token=token)
        response = self.servicer.ValidateToken(req, self.context)
        self.assertTrue(response.valid)
        self.assertEqual(response.user_id, self.user.id)

    def test_t9_create_user_duplicate_via_service(self):
        user, error = create_user_account(
            email='grpc@test.local',
            nombre='Dup',
            rol='alumno',
            password='AlumnoPass123!',
        )
        self.assertIsNone(user)
        self.assertIn('registrado', error.lower())

    def test_create_user_grpc_success(self):
        req = auth_pb2.CreateUserRequest(
            email='nuevo-grpc@test.local',
            nombre='Nuevo GRPC',
            rol='alumno',
            password='AlumnoPass123!',
        )
        response = self.servicer.CreateUser(req, self.context)
        self.assertTrue(response.success)
        self.assertTrue(User.objects.filter(email='nuevo-grpc@test.local').exists())
