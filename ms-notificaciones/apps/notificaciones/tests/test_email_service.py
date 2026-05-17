from django.core import mail
from django.test import TestCase, override_settings

from apps.notificaciones.models import HistorialCorreo, TipoCorreo
from apps.notificaciones.services.data_provider import (
    AlumnoData,
    DocenteData,
    MateriaData,
    NotificacionesDataProvider,
)
from apps.notificaciones.services.email_service import EmailService


class FixedDataProvider(NotificacionesDataProvider):
    """Datos fijos para tests sin gRPC."""

    def get_alumno(self, alumno_id: int):
        if alumno_id == 999:
            return None
        return AlumnoData(
            id=alumno_id,
            nombre='Ana Pérez',
            matricula='20240001',
            email='ana@test.local',
        )

    def get_materia(self, materia_id: int):
        if materia_id == 999:
            return None
        return MateriaData(
            id=materia_id,
            nombre='Programación Web',
            nrc='12345',
            seccion='B',
            periodo_nombre='Primavera 2026',
        )

    def get_docente_by_usuario_id(self, usuario_id: int):
        if usuario_id == 999:
            return None
        return DocenteData(
            usuario_id=usuario_id,
            nombre='Dr. García',
            email='docente@test.local',
        )

    def get_alumnos_by_materia(self, materia_id: int):
        return [
            AlumnoData(1, 'Ana Pérez', '20240001', 'ana@test.local'),
            AlumnoData(2, 'Luis López', '20240002', 'luis@test.local'),
        ]


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='AGM Test <test@agm.local>',
)
class EmailServiceTests(TestCase):
    def setUp(self):
        self.service = EmailService(data_provider=FixedDataProvider())

    def test_send_bienvenida_ok(self):
        result = self.service.send_bienvenida(1, 10, 'ClaveTemp123')
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Programación Web', mail.outbox[0].subject)
        self.assertIn('ana@test.local', mail.outbox[0].to)
        self.assertTrue(
            HistorialCorreo.objects.filter(
                tipo=TipoCorreo.BIENVENIDA, exitoso=True
            ).exists()
        )

    def test_send_bienvenida_alumno_no_encontrado(self):
        result = self.service.send_bienvenida(999, 10, 'x')
        self.assertFalse(result['success'])
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(
            HistorialCorreo.objects.filter(
                tipo=TipoCorreo.BIENVENIDA, exitoso=False
            ).exists()
        )

    def test_send_baja_ok(self):
        result = self.service.send_baja(1, 5, 10)
        self.assertTrue(result['success'])
        self.assertEqual(mail.outbox[0].to, ['docente@test.local'])
        self.assertIn('Ana Pérez', mail.outbox[0].alternatives[0][0])

    def test_send_reset_password_ok(self):
        url = 'http://localhost:4200/reset-password?token=abc'
        result = self.service.send_reset_password('user@test.local', 'abc', url)
        self.assertTrue(result['success'])
        self.assertIn(url, mail.outbox[0].alternatives[0][0])

    def test_send_cierre_materia_multiple(self):
        result = self.service.send_cierre_materia(10)
        self.assertTrue(result['success'])
        self.assertEqual(result['enviados'], 2)
        self.assertEqual(result['fallidos'], 0)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            HistorialCorreo.objects.filter(
                tipo=TipoCorreo.CIERRE_MATERIA, exitoso=True
            ).count(),
            2,
        )
