from unittest.mock import patch

from django.test import TestCase

from apps.core.models import EstadoMateria


class CerrarMateriaTests(TestCase):
    @patch('apps.core.views.send_cierre_materia', return_value=True)
    def test_cerrar_materia_ok(self, mock_send):
        response = self.client.post('/materias/10/cerrar')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertTrue(body['data']['notificacion_enviada'])
        mock_send.assert_called_once_with(10)
        estado = EstadoMateria.objects.get(materia_id=10)
        self.assertTrue(estado.cerrada)
        self.assertTrue(estado.notificacion_enviada)

    @patch('apps.core.views.send_cierre_materia', return_value=False)
    def test_cerrar_materia_ms6_caido_no_aborta(self, mock_send):
        response = self.client.post('/materias/11/cerrar')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(EstadoMateria.objects.get(materia_id=11).cerrada)
        self.assertFalse(response.json()['data']['notificacion_enviada'])
