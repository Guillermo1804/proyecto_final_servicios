import os
import sys
import grpc
from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch

from utils.jwt_local import AuthenticatedUser
from apps.core.models import Periodo


def _admin_user():
    return AuthenticatedUser(
        user_id=1,
        email="test@buap.mx",
        rol="admin",
        nombre="Test",
    )


class PeriodoCRUDTests(TestCase):
    """Tests para CRUD de Periodo y constraint de unicidad de activo."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        self.patcher = patch("utils.jwt_local.validate_access_token")
        self.mock_validate = self.patcher.start()
        self.mock_validate.return_value = _admin_user()

    def tearDown(self):
        self.patcher.stop()

    # ── Test 1: crear periodo válido retorna 201 ───────────────────────
    def test_crear_periodo_valido_retorna_201(self):
        """POST /api/periodos/ con datos válidos debe retornar 201."""
        payload = {
            "nombre": "Primavera 2026",
            "fecha_inicio": "2026-02-01",
            "fecha_fin": "2026-06-30",
        }
        response = self.client.post(
            "/api/periodos/", data=payload, format="json"
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["nombre"], "Primavera 2026")
        self.assertFalse(body["data"]["activo"])
        # Verificar que se creó en la BD
        self.assertEqual(Periodo.objects.count(), 1)

    # ── Test 2: activar periodo desactiva el anterior ──────────────────
    def test_activar_periodo_desactiva_anterior(self):
        """
        Al activar un segundo periodo, el primero debe desactivarse.
        Solo un periodo puede estar activo a la vez.
        """
        # Crear dos periodos inactivos
        p1 = Periodo.objects.create(
            nombre="Otoño 2025",
            fecha_inicio="2025-08-01",
            fecha_fin="2025-12-15",
        )
        p2 = Periodo.objects.create(
            nombre="Primavera 2026",
            fecha_inicio="2026-02-01",
            fecha_fin="2026-06-30",
        )

        # Activar el primero
        resp1 = self.client.post(f"/api/periodos/{p1.pk}/activar/")
        self.assertEqual(resp1.status_code, 200)
        p1.refresh_from_db()
        self.assertTrue(p1.activo)

        # Activar el segundo — el primero debe desactivarse
        resp2 = self.client.post(f"/api/periodos/{p2.pk}/activar/")
        self.assertEqual(resp2.status_code, 200)
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertFalse(p1.activo)
        self.assertTrue(p2.activo)

        # Verificar a nivel BD: solo un activo
        activos = Periodo.objects.filter(activo=True).count()
        self.assertEqual(activos, 1)

    # ── Test 3: Import PDF válido ───────────────────────────────────────────
    def test_importar_materias_pdf_valido_retorna_200(self):
        """POST /api/periodos/{id}/importar-materias/ con PDF válido."""
        p = Periodo.objects.create(
            nombre="Otoño 2026",
            fecha_inicio="2026-08-01",
            fecha_fin="2026-12-15",
            activo=False
        )
        
        import os
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        fixture_path = "test-data/fixture.pdf"
        
        if not os.path.exists(fixture_path):
            self.skipTest("Fixture PDF no encontrado, omitiendo prueba")

        with open(fixture_path, "rb") as f:
            archivo = SimpleUploadedFile("PA.pdf", f.read(), content_type="application/pdf")
            
        response = self.client.post(
            f"/api/periodos/{p.pk}/importar-materias/",
            {"archivo": archivo},
            format="multipart"
        )
        
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIn("creadas", body["data"])
        self.assertIn("actualizadas", body["data"])
        self.assertIn("errores", body["data"])
        self.assertGreater(body["data"]["creadas"], 0)

    # ── Test 4: Filas malformadas ──────────────────────────────────────────
    from unittest.mock import patch
    @patch('utils.pdf_parser.parsear_pdf_materias')
    def test_importar_materias_tolerante_a_fallos(self, mock_parsear):
        """Simulamos un PDF donde hay filas válidas y errores (tolerancia)."""
        p = Periodo.objects.create(
            nombre="Primavera 2027",
            fecha_inicio="2027-02-01",
            fecha_fin="2027-06-30",
        )
        
        materias_mock = [
            {
                "nrc": "12345",
                "clave": "CCO123",
                "nombre": "Prog 1",
                "seccion": "100",
                "docente_nombre": "Juan",
                "horario": "L 10-12"
            }
        ]
        errores_count = 2
        mock_parsear.return_value = (materias_mock, errores_count)
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        archivo = SimpleUploadedFile("dummy.pdf", b"%PDF-1.4 dummy file", content_type="application/pdf")
        
        response = self.client.post(
            f"/api/periodos/{p.pk}/importar-materias/",
            {"archivo": archivo},
            format="multipart"
        )
        
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["creadas"], 1)
        self.assertEqual(body["data"]["errores"], 2)

    def test_get_periodo_activo(self):
        """GET /api/periodos/activo/ debe retornar el periodo activo o 404 si no hay."""
        # Limpiar
        Periodo.objects.all().delete()
        
        # Caso 1: No hay activo
        response = self.client.get("/api/periodos/activo/")
        self.assertEqual(response.status_code, 404)
        
        # Caso 2: Hay activo
        p = Periodo.objects.create(
            nombre="Activo Now", 
            fecha_inicio="2026-01-01", 
            fecha_fin="2026-06-30", 
            activo=True
        )
        response = self.client.get("/api/periodos/activo/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["data"]["activo"])
        self.assertEqual(body["data"]["nombre"], "Activo Now")

    # ── Test 5: request sin Authorization header retorna 401 ──────────
    def test_request_sin_auth_header_retorna_401(self):
        """Un endpoint protegido sin header de autenticación debe retornar 401."""
        self.client.credentials()
        response = self.client.post("/api/periodos/", data={}, format="json")
        self.assertEqual(response.status_code, 401)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["message"], "Token requerido")

    # ── Test 6: request con rol incorrecto retorna 403 ─────────────────
    def test_request_rol_incorrecto_retorna_403(self):
        """Un usuario con rol no autorizado (ej. alumno) debe recibir 403 en ruta de admin."""
        self.mock_validate.return_value = AuthenticatedUser(
            user_id=2,
            email="alumno@buap.mx",
            rol="alumno",
            nombre="Alumno Test",
        )
        payload = {
            "nombre": "Primavera 2026",
            "fecha_inicio": "2026-02-01",
            "fecha_fin": "2026-06-30",
        }
        response = self.client.post("/api/periodos/", data=payload, format="json")
        self.assertEqual(response.status_code, 403)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["message"], "Sin permisos")


class MateriaCRUDTests(TestCase):
    """Tests para CRUD de Materia y sus filtros/paginación."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        self.patcher = patch("utils.jwt_local.validate_access_token")
        self.mock_validate = self.patcher.start()
        self.mock_validate.return_value = _admin_user()

        self.periodo = Periodo.objects.create(
            nombre="Periodo Prueba",
            fecha_inicio="2026-01-01",
            fecha_fin="2026-06-30"
        )

    def tearDown(self):
        self.patcher.stop()

    def test_list_materias_paginado(self):
        """El listado debe retornar el envelope de paginación AGM con count y results."""
        from apps.core.models import Materia
        for i in range(15):
            Materia.objects.create(
                periodo=self.periodo,
                nrc=f"100{i:02d}",
                nombre=f"Materia {i}",
                clave=f"C{i}",
                seccion="1"
            )
            
        response = self.client.get(f"/api/materias/?periodo_id={self.periodo.pk}")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIn("count", body["data"])
        self.assertIn("results", body["data"])
        self.assertEqual(body["data"]["count"], 15)
        self.assertEqual(len(body["data"]["results"]), 10)  # default limit es 10

    def test_filtro_nombre(self):
        """Filtro ?nombre= debe retornar solo coincidencias y un param extraño debe dar 400."""
        from apps.core.models import Materia
        Materia.objects.create(periodo=self.periodo, nrc="111", nombre="Matematicas Basicas", clave="M1", seccion="1")
        Materia.objects.create(periodo=self.periodo, nrc="222", nombre="Fisica Cuantica", clave="F1", seccion="1")
        Materia.objects.create(periodo=self.periodo, nrc="333", nombre="Matematicas Avanzadas", clave="M2", seccion="1")
        
        # Filtro exitoso
        resp1 = self.client.get("/api/materias/?nombre=Matematicas")
        self.assertEqual(resp1.status_code, 200)
        body1 = resp1.json()
        self.assertEqual(body1["data"]["count"], 2)
        
        # Filtro con parámetro no reconocido debe fallar (400)
        resp2 = self.client.get("/api/materias/?fake_param=123")
        self.assertEqual(resp2.status_code, 400)
        body2 = resp2.json()
        self.assertFalse(body2["success"])
        self.assertIn("no reconocido", body2["message"])

    def test_crear_materia_retorna_201(self):
        """Crear una materia vía POST debe retornar 201 y su envelope."""
        payload = {
            "periodo": self.periodo.pk,
            "nrc": "99999",
            "nombre": "Test",
            "seccion": "A",
            "clave": "TEST01",
            "docente_nombre": "Doe",
            "horario": "L 07:00-09:00"
        }
        response = self.client.post("/api/materias/", data=payload, format="json")
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["nrc"], "99999")
        self.assertEqual(body["data"]["nombre"], "Test")

    def test_paginacion_page_and_limit(self):
        """Verificar que ?page=1&limit=5 funciona correctamente."""
        from apps.core.models import Materia
        for i in range(10):
            Materia.objects.create(
                periodo=self.periodo,
                nrc=f"500{i:02d}",
                nombre=f"Materia Test Paginacion {i}",
                clave=f"CP{i}",
                seccion="1"
            )
            
        response = self.client.get("/api/materias/?page=1&limit=5")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["data"]["results"]), 5)
        self.assertGreaterEqual(body["data"]["count"], 10)


from unittest.mock import MagicMock
from proto_generated import periodos_pb2
from grpc_server.servicer import PeriodosServicer

class PeriodosGRPCTests(TestCase):
    """Tests unitarios para el Servicer gRPC de Periodos."""

    def setUp(self):
        self.servicer = PeriodosServicer()
        # Limpiar y crear periodo activo
        Periodo.objects.all().delete()
        self.periodo = Periodo.objects.create(
            nombre="Periodo Activo Test",
            fecha_inicio="2026-01-01",
            fecha_fin="2026-06-30",
            activo=True
        )

    def test_grpc_get_periodo_activo(self):
        """GetPeriodoActivo debe retornar los datos del periodo con activo=True."""
        request = periodos_pb2.Empty()
        context = MagicMock()
        response = self.servicer.GetPeriodoActivo(request, context)
        
        self.assertEqual(response.id, self.periodo.id)
        self.assertEqual(response.nombre, "Periodo Activo Test")
        self.assertTrue(response.activo)

    def test_grpc_get_materia_by_id_not_found(self):
        """GetMateriaById con ID inexistente debe llamar a context.abort con NOT_FOUND."""
        request = periodos_pb2.GetMateriaByIdRequest(materia_id=99999)
        context = MagicMock()
        
        self.servicer.GetMateriaById(request, context)
        
        # Verificar que se llamó a abort con StatusCode.NOT_FOUND
        context.abort.assert_called_once()
        args, _ = context.abort.call_args
        self.assertEqual(args[0], grpc.StatusCode.NOT_FOUND)


