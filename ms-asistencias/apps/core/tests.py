"""Tests REST MS-5 Asistencias."""

import base64
import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import SesionAsistencia, RegistroAsistencia
from apps.core.utils import sign_qr_payload


LOC_MEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}


def _auth_headers():
    return {"HTTP_AUTHORIZATION": "Bearer test-token"}


@override_settings(CACHES=LOC_MEM_CACHE)
class SesionAsistenciaAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.auth_patcher = patch("apps.core.authentication.validate_token")
        self.mock_validate = self.auth_patcher.start()
        self.mock_validate.return_value = {
            "user_id": 7,
            "role": "docente",
            "email": "doc@buap.mx",
        }

    def tearDown(self):
        self.auth_patcher.stop()

    def test_iniciar_sesion_sin_token_retorna_401(self):
        response = self.client.post(
            "/api/sesiones/iniciar/",
            {"materia_id": 1, "docente_id": 7},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))

    @patch("apps.core.utils.store_sesion_in_redis", return_value=True)
    @patch("apps.core.utils.initialize_stats", return_value=True)
    def test_iniciar_sesion_ok(self, _init_stats, _store_redis):
        response = self.client.post(
            "/api/sesiones/iniciar/",
            {"materia_id": 10, "docente_id": 7},
            format="json",
            **_auth_headers(),
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(SesionAsistencia.objects.filter(materia_id=10, activa=True).exists())

    @patch("apps.core.utils.store_sesion_in_redis", return_value=True)
    @patch("apps.core.utils.initialize_stats", return_value=True)
    def test_sesion_activa_por_materia(self, _init_stats, _store_redis):
        self.client.post(
            "/api/sesiones/iniciar/",
            {"materia_id": 11, "docente_id": 7},
            format="json",
            **_auth_headers(),
        )
        response = self.client.get("/api/sesiones/activa/?materia_id=11", **_auth_headers())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["activa"])

    @patch("apps.core.utils.store_sesion_in_redis", return_value=True)
    @patch("apps.core.utils.initialize_stats", return_value=True)
    def test_cerrar_sesion(self, _init_stats, _store_redis):
        create = self.client.post(
            "/api/sesiones/iniciar/",
            {"materia_id": 12, "docente_id": 7},
            format="json",
            **_auth_headers(),
        )
        sesion_id = create.json()["sesion"]["id"]
        response = self.client.delete(f"/api/sesiones/{sesion_id}/cerrar/", **_auth_headers())
        self.assertEqual(response.status_code, 200)
        sesion = SesionAsistencia.objects.get(id=sesion_id)
        self.assertFalse(sesion.activa)

    @patch("apps.core.utils.store_sesion_in_redis", return_value=True)
    @patch("apps.core.utils.initialize_stats", return_value=True)
    def test_stats_sesion(self, _init_stats, _store_redis):
        create = self.client.post(
            "/api/sesiones/iniciar/",
            {"materia_id": 13, "docente_id": 7},
            format="json",
            **_auth_headers(),
        )
        sesion_id = create.json()["sesion"]["id"]
        sesion = SesionAsistencia.objects.get(id=sesion_id)
        RegistroAsistencia.objects.create(
            sesion=sesion, alumno_id=1, estado="presente", minuto_registro=0
        )
        RegistroAsistencia.objects.create(
            sesion=sesion, alumno_id=2, estado="retardo", minuto_registro=6
        )
        response = self.client.get(f"/api/sesiones/{sesion_id}/stats/", **_auth_headers())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["presentes"], 1)
        self.assertEqual(body["retardos"], 1)


@override_settings(CACHES=LOC_MEM_CACHE)
class RegistroQRTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.auth_patcher = patch("apps.core.authentication.validate_token")
        self.mock_validate = self.auth_patcher.start()
        self.mock_validate.return_value = {
            "user_id": 7,
            "role": "docente",
            "email": "doc@buap.mx",
        }
        self.sesion = SesionAsistencia.objects.create(
            materia_id=20,
            docente_id=7,
            fecha_fin_teorica=timezone.now() + timedelta(minutes=10),
            estado="activa",
            activa=True,
        )

    def tearDown(self):
        self.auth_patcher.stop()

    @patch("apps.core.qr_service.is_alumno_en_materia", return_value=True)
    def test_generar_qr_y_registrar(self, _enrolled):
        gen = self.client.get(
            "/api/qr/generate/?materia_id=20&alumno_id=5",
            **_auth_headers(),
        )
        self.assertEqual(gen.status_code, 200)
        encoded = gen.json()["encoded_payload"]

        reg = self.client.post(
            "/api/asistencias/registrar/",
            {"encoded_payload": encoded},
            format="json",
            **_auth_headers(),
        )
        self.assertEqual(reg.status_code, 201)
        self.assertTrue(
            RegistroAsistencia.objects.filter(sesion=self.sesion, alumno_id=5).exists()
        )

    def test_registrar_qr_duplicado_falla(self):
        payload = {
            "alumno_id": 6,
            "sesion_id": self.sesion.id,
            "materia_id": 20,
            "timestamp": timezone.now().timestamp(),
        }
        payload["signature"] = sign_qr_payload({k: v for k, v in payload.items()})
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()

        first = self.client.post(
            "/api/asistencias/registrar/",
            {"encoded_payload": encoded},
            format="json",
            **_auth_headers(),
        )
        self.assertEqual(first.status_code, 201)

        second = self.client.post(
            "/api/asistencias/registrar/",
            {"encoded_payload": encoded},
            format="json",
            **_auth_headers(),
        )
        self.assertEqual(second.status_code, 400)

    @patch("apps.core.alumno_enrichment.get_alumno_by_id")
    def test_list_registros_por_sesion(self, mock_get_alumno):
        from apps.core.alumno_enrichment import clear_alumno_cache

        clear_alumno_cache()
        mock_alumno = MagicMock()
        mock_alumno.nombre = "Ana López"
        mock_alumno.matricula = "202600001"
        mock_get_alumno.return_value = mock_alumno

        RegistroAsistencia.objects.create(
            sesion=self.sesion,
            alumno_id=8,
            estado="presente",
            minuto_registro=1,
        )
        response = self.client.get(
            f"/api/registros/?sesion_id={self.sesion.id}",
            **_auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(isinstance(data, list))
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["alumno_nombre"], "Ana López")
        self.assertEqual(data[0]["matricula"], "202600001")
