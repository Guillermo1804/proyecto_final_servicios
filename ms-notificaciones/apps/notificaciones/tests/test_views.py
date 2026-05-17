import os
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
@patch.dict(
    os.environ,
    {
        'INTERNAL_API_KEY': 'test-internal-key',
        'USE_PLACEHOLDER_DATA': 'True',
    },
    clear=False,
)
class NotificacionesViewsTests(TestCase):
    """Env INTERNAL_API_KEY debe coincidir con la cabecera de las peticiones autorizadas."""
    def setUp(self):
        self.client = APIClient()
        self.headers = {'HTTP_X_INTERNAL_API_KEY': 'test-internal-key'}

    def test_bienvenida_requires_auth(self):
        response = self.client.post(
            '/notificaciones/bienvenida',
            {'alumno_id': 1, 'materia_id': 10, 'clave_acceso': 'x'},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()['success'])

    def test_bienvenida_ok(self):
        response = self.client.post(
            '/notificaciones/bienvenida',
            {'alumno_id': 1, 'materia_id': 10, 'clave_acceso': 'Clave123'},
            format='json',
            **self.headers,
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertIn('historial_id', body['data'])

    def test_bienvenida_invalid_payload(self):
        response = self.client.post(
            '/notificaciones/bienvenida',
            {'materia_id': 10},
            format='json',
            **self.headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertIn('clave_acceso', response.json()['errors'])

    def test_reset_password_ok(self):
        response = self.client.post(
            '/notificaciones/reset-password',
            {
                'email': 'user@test.local',
                'token': 'abc',
                'reset_url': 'http://localhost:4200/reset?token=abc',
            },
            format='json',
            **self.headers,
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['success'])

    def test_cierre_materia_ok(self):
        response = self.client.post(
            '/notificaciones/cierre-materia',
            {'materia_id': 5},
            format='json',
            **self.headers,
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertGreaterEqual(body['data']['enviados'], 1)
