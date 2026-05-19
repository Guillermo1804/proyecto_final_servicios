import os
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import PasswordResetToken

User = get_user_model()

TEST_SECRET = 'test-secret-key-for-jwt-ms1-32bytes!!'
TEST_ENV = {
    'INTERNAL_API_KEY': 'test-internal-key',
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


@patch.dict(os.environ, TEST_ENV, clear=False)
class AuthRestTests(TestCase):
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
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email='admin@test.local',
            nombre='Admin Test',
            rol='admin',
            password='AdminPass123!',
        )
        self.alumno = User.objects.create_user(
            email='alumno@test.local',
            nombre='Alumno Test',
            rol='alumno',
            password='AlumnoPass123!',
        )

    def _login(self, email, password):
        return self.client.post(
            '/auth/login',
            {'email': email, 'password': password},
            format='json',
        )

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        access['user_id'] = user.id
        access['email'] = user.email
        access['rol'] = user.rol
        access['nombre'] = user.nombre
        return {'HTTP_AUTHORIZATION': f'Bearer {access}'}

    def test_t1_login_admin(self):
        response = self._login('admin@test.local', 'AdminPass123!')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertIn('access_token', body['data'])
        self.assertIn('refresh_token', body['data'])
        self.assertEqual(body['data']['user']['rol'], 'admin')

    def test_t2_me_without_token(self):
        response = self.client.get('/auth/me')
        self.assertEqual(response.status_code, 401)

    def test_t3_refresh_valid(self):
        login = self._login('admin@test.local', 'AdminPass123!')
        refresh = login.json()['data']['refresh_token']
        response = self.client.post(
            '/auth/refresh-token',
            {'refresh': refresh},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json()['data'])

    def test_t4_logout_blacklists_refresh(self):
        login = self._login('admin@test.local', 'AdminPass123!')
        refresh = login.json()['data']['refresh_token']
        logout = self.client.post(
            '/auth/logout',
            {'refresh': refresh},
            format='json',
            **self._auth_header(self.admin),
        )
        self.assertEqual(logout.status_code, 200)
        reuse = self.client.post(
            '/auth/refresh-token',
            {'refresh': refresh},
            format='json',
        )
        self.assertEqual(reuse.status_code, 401)

    @patch('apps.core.views.send_reset_password_notification')
    def test_t5_forgot_password_always_200(self, mock_send):
        response = self.client.post(
            '/auth/forgot-password',
            {'email': 'admin@test.local'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        mock_send.assert_called_once()

    def test_t6_reset_password_valid(self):
        token = PasswordResetToken.objects.create(
            user=self.admin,
            token=uuid4(),
            expira_en=timezone.now() + timedelta(hours=1),
        )
        response = self.client.post(
            '/auth/reset-password',
            {'token': str(token.token), 'password': 'NuevaPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('NuevaPass123!'))

    def test_t7_reset_token_reused(self):
        token = PasswordResetToken.objects.create(
            user=self.admin,
            token=uuid4(),
            expira_en=timezone.now() + timedelta(hours=1),
            usado=True,
        )
        response = self.client.post(
            '/auth/reset-password',
            {'token': str(token.token), 'password': 'OtraPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_t10_alumno_cannot_list_usuarios(self):
        response = self.client.get('/usuarios', **self._auth_header(self.alumno))
        self.assertEqual(response.status_code, 403)

    def test_post_usuarios_internal_api_key(self):
        response = self.client.post(
            '/usuarios',
            {
                'email': 'nuevo@test.local',
                'nombre': 'Nuevo Usuario',
                'rol': 'docente',
                'password': 'TempPass123!',
                'send_email': False,
            },
            format='json',
            HTTP_X_INTERNAL_API_KEY='test-internal-key',
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email='nuevo@test.local').exists())

    def test_post_usuarios_duplicate_email(self):
        payload = {
            'email': 'admin@test.local',
            'nombre': 'Duplicado',
            'rol': 'docente',
            'password': 'TempPass123!',
            'send_email': False,
        }
        response = self.client.post(
            '/usuarios',
            payload,
            format='json',
            HTTP_X_INTERNAL_API_KEY='test-internal-key',
        )
        self.assertEqual(response.status_code, 400)
