"""Confirmación de sesión tras cerrar el escaneo (MS-5)."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.core.models import SesionAsistencia
from apps.core.services import SesionAsistenciaService


class ConfirmarSesionTrasCerrarTests(TestCase):
    def setUp(self):
        ahora = timezone.now()
        self.sesion = SesionAsistencia.objects.create(
            materia_id=1,
            docente_id=1,
            fecha_fin_teorica=ahora + timedelta(minutes=10),
            estado='activa',
            activa=True,
        )

    def test_confirmar_despues_de_cerrar(self):
        ok_cerrar, _ = SesionAsistenciaService.cerrar_sesion(self.sesion.id)
        self.assertTrue(ok_cerrar)

        self.sesion.refresh_from_db()
        self.assertFalse(self.sesion.activa)
        self.assertEqual(self.sesion.estado, 'cerrada')

        ok_confirmar, msg = SesionAsistenciaService.confirmar_sesion(self.sesion.id)
        self.assertTrue(ok_confirmar, msg)

        self.sesion.refresh_from_db()
        self.assertEqual(self.sesion.estado, 'confirmada')
        self.assertFalse(self.sesion.activa)
