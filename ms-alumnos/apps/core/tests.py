import os

import grpc
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase, override_settings
from unittest.mock import MagicMock, patch
from rest_framework.test import APIClient

from apps.core.models import Alumno, Docente, EventOutbox, InscripcionMateria, PendingUserCreation
from grpc_server.servicer import AlumnosServicer
from proto_generated import alumnos_pb2, alumnos_pb2_grpc
from utils.jwt_local import AuthenticatedUser


def _admin_user():
    return AuthenticatedUser(
        user_id=1,
        email="test@buap.mx",
        rol="admin",
        nombre="Test",
    )


def _install_jwt_mock(test_case):
    # jwt_required importa validate_access_token en utils.auth (referencia local).
    test_case.patcher = patch("utils.auth.validate_access_token")
    test_case.mock_validate = test_case.patcher.start()
    test_case.mock_validate.return_value = _admin_user()

class AlumnoModelTests(TestCase):
    """Pruebas básicas para el modelo Alumno."""
    
    def test_crear_alumno_valido(self):
        """Verifica que un alumno se persista correctamente."""
        alumno = Alumno.objects.create(
            usuario_id=1,
            matricula="202012345",
            nombre="Juan",
            apellido="Perez",
            email="juan@alumno.buap.mx",
            carrera="Ingeniería en Ciencias de la Computación",
            semestre=5
        )
        self.assertEqual(Alumno.objects.count(), 1)
        self.assertEqual(alumno.matricula, "202012345")
        self.assertTrue(alumno.activo)

class InscripcionModelTests(TestCase):
    """Pruebas para inscripciones y sus restricciones."""

    def setUp(self):
        self.alumno = Alumno.objects.create(
            usuario_id=100,
            matricula="202000000",
            nombre="Test",
            apellido="User",
            email="test@alumno.buap.mx"
        )

    def test_inscripcion_duplicada_activa_falla(self):
        """Inscribir al mismo alumno en la misma materia (ambas activas) debe fallar."""
        # Primera inscripción activa
        InscripcionMateria.objects.create(
            alumno=self.alumno,
            materia_id=1,
            nrc="10001",
            nombre_materia="Matemáticas",
            docente_nombre="Docente A",
            activa=True
        )
        
        # Segunda inscripción activa al mismo alumno/materia_id debe lanzar IntegrityError
        with self.assertRaises(IntegrityError):
            InscripcionMateria.objects.create(
                alumno=self.alumno,
                materia_id=1,
                nrc="10001",
                nombre_materia="Matemáticas",
                docente_nombre="Docente A",
                activa=True
            )

    def test_re_inscripcion_despues_de_baja_funciona(self):
        """Si la inscripción anterior está inactiva, debe permitir una nueva."""
        # Primera inscripción que luego se da de baja
        InscripcionMateria.objects.create(
            alumno=self.alumno,
            materia_id=2,
            nrc="20002",
            nombre_materia="Física",
            docente_nombre="Docente B",
            activa=False # Simulamos baja
        )
        
        # Nueva inscripción activa debe funcionar
        insc = InscripcionMateria.objects.create(
            alumno=self.alumno,
            materia_id=2,
            nrc="20002",
            nombre_materia="Física",
            docente_nombre="Docente B",
            activa=True
        )
        self.assertEqual(InscripcionMateria.objects.filter(alumno=self.alumno, materia_id=2).count(), 2)
        self.assertTrue(insc.activa)


class DocenteCRUDTests(TestCase):
    """Tests para CRUD de Docente y sus filtros/paginación."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        _install_jwt_mock(self)

        # Crear 15 docentes para probar paginación
        for i in range(15):
            Docente.objects.create(
                usuario_id=1000 + i,
                nombre=f"Docente {i}",
                apellido=f"Apellido {i}",
                email=f"docente{i}@fcc.buap.mx",
                departamento="IA" if i % 2 == 0 else "Computación"
            )

    def tearDown(self):
        self.patcher.stop()

    def test_list_docentes_paginado(self):
        """Listar docentes debe retornar envelope AGM con count y 10 resultados por página."""
        response = self.client.get("/api/docentes/?page=1&limit=5")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["count"], 15)
        self.assertEqual(len(body["data"]["results"]), 5)

    def test_filtro_nombre(self):
        """Filtro ?nombre= debe retornar coincidencias parciales."""
        response = self.client.get("/api/docentes/?nombre=Docente 1")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        # Docente 1, Docente 10, Docente 11, Docente 12, Docente 13, Docente 14
        self.assertGreaterEqual(body["data"]["count"], 6)

    def test_buscar_por_apellido_o_nombre_parcial(self):
        """?buscar= debe coincidir en nombre, apellido, correo o departamento."""
        Docente.objects.create(
            usuario_id=4242,
            nombre="Yael",
            apellido="Mendes Sánchez Ruiz",
            email="yael.mendes@fcc.buap.mx",
            departamento="Computación",
        )

        for term in ("Mendes", "Ruiz", "Yael", "mendes", "fcc.buap"):
            with self.subTest(term=term):
                response = self.client.get(f"/api/docentes/?buscar={term}")
                self.assertEqual(response.status_code, 200)
                emails = [r["email"] for r in response.json()["data"]["results"]]
                self.assertIn("yael.mendes@fcc.buap.mx", emails)

        response = self.client.get("/api/docentes/?buscar=Yael Mendes")
        self.assertEqual(response.status_code, 200)
        emails = [r["email"] for r in response.json()["data"]["results"]]
        self.assertIn("yael.mendes@fcc.buap.mx", emails)

    @patch("apps.core.services.docente_provision.create_user_in_auth", return_value=(7777, None))
    def test_activar_docente_vincula_usuario(self, _mock_create):
        docente = Docente.objects.create(
            usuario_id=None,
            nombre="Ana",
            apellido="Lopez",
            email="ana.lopez@fcc.buap.mx",
            departamento="IA",
        )
        response = self.client.post(f"/api/docentes/{docente.id}/activar-usuario/")
        self.assertEqual(response.status_code, 200)
        docente.refresh_from_db()
        self.assertEqual(docente.usuario_id, 7777)

    def test_crear_docente_retorna_201(self):
        """POST /api/docentes/ con datos válidos crea el registro."""
        data = {
            "usuario_id": 9999,
            "nombre": "Ana",
            "apellido": "López",
            "email": "ana@fcc.buap.mx",
            "departamento": "IA"
        }
        response = self.client.post("/api/docentes/", data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["data"]["nombre"], "Ana")
        self.assertEqual(body["data"]["usuario_id"], 9999)

    def test_crear_docente_sin_auth_retorna_401(self):
        self.client.credentials()
        response = self.client.post("/api/docentes/", data={}, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])

    def test_crear_docente_rol_alumno_retorna_403(self):
        self.mock_validate.return_value = AuthenticatedUser(
            user_id=2,
            email="alumno@buap.mx",
            rol="alumno",
            nombre="Test",
        )
        response = self.client.post("/api/docentes/", data={}, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])


class AlumnoImportTests(TestCase):
    """Tests para POST /api/alumnos/importar/ (PDF lista de clase)."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        _install_jwt_mock(self)

    def tearDown(self):
        self.patcher.stop()

    @override_settings(USE_EVENT_BUS=True)
    @patch("apps.core.views.resolve_materia_context")
    @patch("apps.core.views.parse_pdf_alumnos")
    def test_import_pdf_alumnos_exitoso(self, mock_parse_pdf, mock_materia_ctx):
        mock_parse_pdf.return_value = (
            [
                {
                    "matricula": "202224429",
                    "nombre": "ANGEL G.",
                    "apellido": "AGUILAR SALDIVAR",
                    "carrera": "ICC",
                    "semestre": 1,
                }
            ],
            [],
            {"nrc": "50130", "nombre_materia": "Servicios Web"},
        )
        mock_materia_ctx.return_value = {
            "materia_id": 1,
            "periodo_id": 10,
            "docente_email": "doc@buap.mx",
            "docente_nombre": "Doc",
            "materia_nombre": "Servicios Web",
            "nrc": "50130",
            "docente_id": 0,
        }

        pdf_file = SimpleUploadedFile("lista.pdf", b"%PDF-1.4", content_type="application/pdf")
        response = self.client.post(
            "/api/alumnos/importar/",
            {"file": pdf_file, "materia_id": 1},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["creados"], 1)
        self.assertEqual(data["inscritos"], 1)
        self.assertTrue(Alumno.objects.filter(matricula="202224429").exists())

    def test_import_pdf_sin_materia_id_retorna_400(self):
        pdf_file = SimpleUploadedFile("lista.pdf", b"%PDF-1.4", content_type="application/pdf")
        response = self.client.post(
            "/api/alumnos/importar/",
            {"file": pdf_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

    def test_import_pdf_sin_archivo_retorna_400(self):
        response = self.client.post(
            "/api/alumnos/importar/",
            {"materia_id": 1},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

    @patch("apps.core.views.resolve_materia_context")
    @patch("apps.core.views.parse_pdf_alumnos")
    def test_import_preview_no_persiste(self, mock_parse_pdf, mock_materia_ctx):
        mock_parse_pdf.return_value = (
            [
                {
                    "matricula": "202224429",
                    "nombre": "ANGEL G.",
                    "apellido": "AGUILAR SALDIVAR",
                    "email": "angel@buap.mx",
                    "carrera": "ICC",
                    "semestre": 1,
                }
            ],
            [],
            {"nrc": "50130", "nombre_materia": "Servicios Web"},
        )
        mock_materia_ctx.return_value = {
            "materia_id": 1,
            "periodo_id": 10,
            "nrc": "50130",
        }

        pdf_file = SimpleUploadedFile("lista.pdf", b"%PDF-1.4", content_type="application/pdf")
        response = self.client.post(
            "/api/alumnos/importar/preview/",
            {"file": pdf_file, "materia_id": 1},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(len(data["filas"]), 1)
        self.assertEqual(data["filas"][0]["accion"], "nuevo")
        self.assertEqual(data["filas"][0]["inscripcion"], "nueva")
        self.assertEqual(data["resumen"]["nuevos"], 1)
        self.assertFalse(Alumno.objects.filter(matricula="202224429").exists())

    @override_settings(USE_EVENT_BUS=True)
    @patch("apps.core.views.resolve_materia_context")
    def test_confirmar_import_desde_preview(self, mock_materia_ctx):
        mock_materia_ctx.return_value = {
            "materia_id": 1,
            "periodo_id": 10,
            "docente_email": "doc@buap.mx",
            "docente_nombre": "Doc",
            "materia_nombre": "Servicios Web",
            "nrc": "50130",
            "docente_id": 0,
        }
        response = self.client.post(
            "/api/alumnos/importar/confirmar/",
            {
                "materia_id": 1,
                "alumnos": [
                    {
                        "matricula": "202224430",
                        "nombre": "MARIA",
                        "apellido": "LOPEZ",
                        "email": "maria@buap.mx",
                        "carrera": "ICC",
                        "semestre": 1,
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["creados"], 1)
        self.assertTrue(Alumno.objects.filter(matricula="202224430").exists())


class PdfAlumnosParserTests(TestCase):
    """Parser contra ListaAlumnos_Servicios_Web.pdf (ejemplo BUAP)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidates = [
            os.path.join(base, "tests", "fixtures", "ListaAlumnos_Servicios_Web.pdf"),
            os.path.join(base, "..", "ListaAlumnos_Servicios_Web.pdf"),
        ]
        cls.pdf_path = next((p for p in candidates if os.path.isfile(p)), None)

    def test_parse_lista_servicios_web_30_alumnos(self):
        if not self.pdf_path:
            self.skipTest("Fixture ListaAlumnos_Servicios_Web.pdf no encontrado")

        from utils.pdf_alumnos_parser import parse_pdf_alumnos

        rows, errors, meta = parse_pdf_alumnos(self.pdf_path)
        self.assertEqual(len(rows), 30, f"filas={len(rows)}, errors={errors[:5]}")
        self.assertEqual(meta["nrc"], "50130")
        self.assertIn("Servicios Web", meta["nombre_materia"])
        self.assertIn("MENDEZ", meta["docente"].upper())

        angel = next(r for r in rows if r["matricula"] == "202224429")
        self.assertEqual(angel["apellido"], "AGUILAR SALDIVAR")
        self.assertEqual(angel["nombre"], "ANGEL G.")

        incompleto = next(r for r in rows if r["matricula"] == "202227348")
        self.assertEqual(incompleto["nombre"], "HERNANDEZ PALESTINA")

        self.assertEqual(angel["email"], "angel.aguilarsal@alumno.buap.mx")
        emails_ok = sum(1 for r in rows if r.get("email"))
        self.assertEqual(emails_ok, 30, f"emails={emails_ok}, sample err={errors[:3]}")


class AlumnoPorMateriaTests(TestCase):
    """Tests para el endpoint /api/alumnos/por-materia/."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        _install_jwt_mock(self)

        # Crear 3 alumnos
        self.a1 = Alumno.objects.create(usuario_id=1, matricula="20201", nombre="Juan", apellido="Zepeda", email="juan@b.com")
        self.a2 = Alumno.objects.create(usuario_id=2, matricula="20202", nombre="Beto", apellido="Yañez", email="beto@b.com")
        self.a3 = Alumno.objects.create(usuario_id=3, matricula="20203", nombre="Carlos", apellido="Ximenez", email="carlos@b.com")
        
        # Inscribir a1 y a2 en materia 1 (activos)
        InscripcionMateria.objects.create(alumno=self.a1, materia_id=1, nrc="100", nombre_materia="Mate", docente_nombre="Doc1", activa=True)
        InscripcionMateria.objects.create(alumno=self.a2, materia_id=1, nrc="100", nombre_materia="Mate", docente_nombre="Doc1", activa=True)
        
        # Inscribir a3 en materia 1 (inactivo)
        InscripcionMateria.objects.create(alumno=self.a3, materia_id=1, nrc="100", nombre_materia="Mate", docente_nombre="Doc1", activa=False)

    def tearDown(self):
        self.patcher.stop()

    def test_list_por_materia_exitoso(self):
        """GET ?materia_id=1 debe retornar solo 2 alumnos activos, ordenados por apellido."""
        response = self.client.get("/api/alumnos/por-materia/?materia_id=1")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        # Debe haber 2 activos (a1, a2). a3 es inactivo.
        self.assertEqual(body["data"]["count"], 2)
        # Orden: Yañez (a2) < Zepeda (a1)
        self.assertEqual(body["data"]["results"][0]["alumno"]["matricula"], "20202")
        self.assertEqual(body["data"]["results"][1]["alumno"]["matricula"], "20201")

    def test_list_por_materia_sin_id_falla(self):
        """GET sin materia_id debe retornar 400."""
        response = self.client.get("/api/alumnos/por-materia/")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])


class AlumnoBajaMateriaTests(TestCase):
    """Tests para la baja irreversible de materias."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        _install_jwt_mock(self)

        self.alumno = Alumno.objects.create(usuario_id=10, matricula="2020555", nombre="Luis", apellido="Baja", email="luis@b.com")
        self.insc = InscripcionMateria.objects.create(
            alumno=self.alumno, materia_id=5, nrc="500", nombre_materia="Bajas", docente_nombre="D5", activa=True
        )

    def tearDown(self):
        self.patcher.stop()

    @override_settings(USE_EVENT_BUS=True)
    @patch("django.db.transaction.on_commit", side_effect=lambda func: func())
    @patch(
        "apps.core.views.resolve_materia_context",
        return_value={
            "materia_id": 5,
            "periodo_id": 3,
            "docente_email": "doc@buap.mx",
            "docente_id": 99,
            "docente_nombre": "Doc",
            "materia_nombre": "Bajas",
            "nrc": "500",
        },
    )
    def test_baja_materia_exitosa_event_bus(self, _mock_ctx, _mock_on_commit):
        """Baja publica alumno.withdrawn.v1 sin depender de MS-6."""
        payload = {"materia_id": 5}

        response = self.client.post(
            f"/api/alumnos/{self.alumno.id}/baja-materia/",
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        self.insc.refresh_from_db()
        self.assertFalse(self.insc.activa)
        self.assertIsNotNone(self.insc.fecha_baja)
        self.assertEqual(
            EventOutbox.objects.filter(event_name="alumno.withdrawn.v1").count(),
            1,
        )

    def test_baja_materia_ya_inactiva_falla(self):
        """Intentar dar de baja una materia ya inactiva retorna 400."""
        self.insc.activa = False
        self.insc.save()
        
        payload = {"materia_id": 5}
        response = self.client.post(f"/api/alumnos/{self.alumno.id}/baja-materia/", payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "baja ya procesada")


class AlumnoImportMs1ProvisionTests(TestCase):
    """Importacion de alumnos intenta activar MS-1 de forma sincrona."""

    @override_settings(USE_EVENT_BUS=True)
    @patch("apps.core.services.alumno_ms1_sync.provision_alumno_usuario")
    def test_import_batch_activa_ms1_en_creados_y_actualizados(self, mock_provision):
        from apps.core.services.alumno_import import process_alumno_import_batch

        next_user_id = 6001

        def _provision(alumno):
            nonlocal next_user_id
            alumno.usuario_id = next_user_id
            next_user_id += 1
            alumno.save(update_fields=["usuario_id"])
            return alumno, None

        mock_provision.side_effect = _provision

        creados, actualizados, inscritos = process_alumno_import_batch(
            [
                {
                    "matricula": "202211111",
                    "nombre": "Nuevo",
                    "apellido": "Alumno",
                    "email": "nuevo@buap.mx",
                }
            ],
            materia_id=0,
        )
        self.assertEqual(creados, 1)
        self.assertEqual(actualizados, 0)
        self.assertEqual(mock_provision.call_count, 1)
        self.assertEqual(Alumno.objects.get(matricula="202211111").usuario_id, 6001)

        mock_provision.reset_mock()
        creados, actualizados, _ = process_alumno_import_batch(
            [
                {
                    "matricula": "202222222",
                    "nombre": "Sin",
                    "apellido": "Ms1",
                    "email": "sin@buap.mx",
                }
            ],
            materia_id=0,
        )
        self.assertEqual(creados, 1)
        mock_provision.assert_called_once()

        Alumno.objects.filter(matricula="202222222").update(usuario_id=None)
        mock_provision.reset_mock()
        _, actualizados, _ = process_alumno_import_batch(
            [
                {
                    "matricula": "202222222",
                    "nombre": "Sin",
                    "apellido": "Ms1",
                    "email": "sin@buap.mx",
                }
            ],
            materia_id=0,
        )
        self.assertEqual(actualizados, 1)
        mock_provision.assert_called_once()


class AlumnoActivarUsuarioTests(TestCase):
    """POST /api/alumnos/{id}/activar-usuario/ vincula MS-1."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        _install_jwt_mock(self)

    def tearDown(self):
        self.patcher.stop()

    @patch("apps.core.services.alumno_provision.create_user_in_auth", return_value=(8888, None))
    def test_activar_alumno_vincula_usuario(self, _mock_create):
        alumno = Alumno.objects.create(
            usuario_id=None,
            matricula="202299999",
            nombre="Pedro",
            apellido="Garcia",
            email="pedro.garcia@alumno.buap.mx",
        )
        response = self.client.post(f"/api/alumnos/{alumno.id}/activar-usuario/")
        self.assertEqual(response.status_code, 200)
        alumno.refresh_from_db()
        self.assertEqual(alumno.usuario_id, 8888)

    @patch("apps.core.services.alumno_provision.create_user_in_auth", return_value=(8888, None))
    def test_activar_alumno_ya_vinculado_idempotente(self, _mock_create):
        alumno = Alumno.objects.create(
            usuario_id=42,
            matricula="202288888",
            nombre="Ana",
            apellido="Lopez",
            email="ana@alumno.buap.mx",
        )
        response = self.client.post(f"/api/alumnos/{alumno.id}/activar-usuario/")
        self.assertEqual(response.status_code, 200)
        _mock_create.assert_not_called()


class AlumnoDesactivarUsuarioTests(TestCase):
    """POST /api/alumnos/{id}/desactivar-usuario/ desvincula MS-1."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        _install_jwt_mock(self)

    def tearDown(self):
        self.patcher.stop()

    @patch("apps.core.services.alumno_provision.deactivate_user_in_auth", return_value=None)
    def test_desactivar_alumno_limpia_usuario_id(self, _mock_deactivate):
        alumno = Alumno.objects.create(
            usuario_id=999,
            matricula="202277777",
            nombre="Baja",
            apellido="Ms1",
            email="baja@buap.mx",
        )
        response = self.client.post(f"/api/alumnos/{alumno.id}/desactivar-usuario/")
        self.assertEqual(response.status_code, 200)
        alumno.refresh_from_db()
        self.assertIsNone(alumno.usuario_id)


class AlumnosGRPCTests(TestCase):
    """Tests para el servidor gRPC de Alumnos."""

    def setUp(self):
        self.servicer = AlumnosServicer()
        self.alumno = Alumno.objects.create(
            usuario_id=100, matricula="GRPC1", nombre="G", apellido="R", email="g@r.com", carrera="ICC"
        )
        self.insc = InscripcionMateria.objects.create(
            alumno=self.alumno, materia_id=10, nrc="N", nombre_materia="M", docente_nombre="D", activa=True
        )

    def test_get_alumno_by_id_inexistente_retorna_not_found(self):
        """GetAlumnoById con ID inexistente debe retornar StatusCode.NOT_FOUND."""
        request = alumnos_pb2.GetAlumnoByIdRequest(alumno_id=999)
        context = MagicMock()
        
        self.servicer.GetAlumnoById(request, context)
        
        context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)

    def test_is_alumno_en_materia_true(self):
        """IsAlumnoEnMateria retorna true para inscripción activa existente."""
        request = alumnos_pb2.IsAlumnoEnMateriaRequest(
            alumno_id=self.alumno.id,
            materia_id=10
        )
        context = MagicMock()
        
        response = self.servicer.IsAlumnoEnMateria(request, context)
        
        self.assertTrue(response.inscrito)


class NotificacionesClientEnvTests(TestCase):
    @patch.dict(
        os.environ,
        {
            'MS_NOTIFICACIONES_GRPC_HOST': 'ms-notificaciones',
            'MS_NOTIFICACIONES_GRPC_PORT': '50056',
        },
        clear=False,
    )
    @patch('utils.notificaciones_client.block_business_grpc')
    def test_target_from_env(self, _mock_block):
        from utils.notificaciones_client import _notificaciones_target

        self.assertEqual(_notificaciones_target(), 'ms-notificaciones:50056')


from django.core.files.uploadedfile import SimpleUploadedFile

class DocenteImportTests(TestCase):
    """Tests para el endpoint de importación de docentes POST /api/docentes/importar/."""

    def setUp(self):
        self.client = APIClient()
        _install_jwt_mock(self)
        self.patcher_auth = self.patcher

    def tearDown(self):
        self.patcher_auth.stop()

    @override_settings(USE_EVENT_BUS=False)
    @patch("apps.core.views.parse_pdf_docentes")
    @patch("apps.core.services.docente_import.create_user_in_auth")
    def test_import_pdf_docentes_exitoso(self, mock_create_user, mock_parse_pdf):
        """Importar un PDF válido de docentes crea los usuarios e inserta los docentes."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token_admin")
        
        # Mocking PDF parser result
        mock_parse_pdf.return_value = ([
            {
                "nombre": "Evelia",
                "apellido": "Perez Bonilla",
                "email": "evelia.perez@correo.buap.mx",
                "departamento": "Computación"
            },
            {
                "nombre": "Adan",
                "apellido": "Limon Faustino",
                "email": "adan.limon@correo.buap.mx",
                "departamento": "IA"
            }
        ], [])
        
        # Mocking gRPC MS-1 Auth CreateUser response: (user_id, error_message)
        mock_create_user.side_effect = [
            (9001, None),
            (9002, None)
        ]
        
        pdf_file = SimpleUploadedFile("trabajadores.pdf", b"%PDF-1.4...", content_type="application/pdf")
        response = self.client.post("/api/docentes/importar/", {"file": pdf_file}, format="multipart")
        
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["creados"], 2)
        self.assertEqual(body["data"]["omitidos"], 0)
        self.assertEqual(body["data"]["errores"], 0)
        
        # Verificamos que se crearon en la BD
        self.assertTrue(Docente.objects.filter(email="evelia.perez@correo.buap.mx").exists())
        self.assertTrue(Docente.objects.filter(email="adan.limon@correo.buap.mx").exists())

    @override_settings(USE_EVENT_BUS=False)
    @patch("apps.core.views.parse_pdf_docentes")
    @patch("apps.core.services.docente_import.create_user_in_auth")
    def test_import_pdf_docentes_grpc_error_graceful(self, mock_create_user, mock_parse_pdf):
        """Si falla gRPC MS-1 Auth para un docente, se maneja de forma graceful y continúa."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token_admin")
        
        mock_parse_pdf.return_value = ([
            {
                "nombre": "Evelia",
                "apellido": "Perez Bonilla",
                "email": "evelia.perez@correo.buap.mx",
                "departamento": "Computación"
            },
            {
                "nombre": "Adan",
                "apellido": "Limon Faustino",
                "email": "adan.limon@correo.buap.mx",
                "departamento": "IA"
            }
        ], [])
        
        # El primero falla en MS-1 Auth, el segundo tiene éxito
        mock_create_user.side_effect = [
            (None, "MS-1 Auth No Disponible"),
            (9002, None)
        ]
        
        pdf_file = SimpleUploadedFile("trabajadores.pdf", b"%PDF-1.4...", content_type="application/pdf")
        response = self.client.post("/api/docentes/importar/", {"file": pdf_file}, format="multipart")
        
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["creados"], 1)
        self.assertEqual(body["data"]["omitidos"], 0)
        self.assertEqual(body["data"]["errores"], 1)
        
        # Se creó solo el segundo
        self.assertFalse(Docente.objects.filter(email="evelia.perez@correo.buap.mx").exists())
        self.assertTrue(Docente.objects.filter(email="adan.limon@correo.buap.mx").exists())

    def test_import_pdf_docentes_sin_auth_retorna_401(self):
        """Una petición sin JWT válido al endpoint de importar retorna 401."""
        self.client.credentials()  # Sin token
        pdf_file = SimpleUploadedFile("trabajadores.pdf", b"%PDF-1.4...", content_type="application/pdf")
        response = self.client.post("/api/docentes/importar/", {"file": pdf_file}, format="multipart")
        self.assertEqual(response.status_code, 401)


from proto_generated import periodos_pb2

class AlumnoMeMateriasTests(TestCase):
    """Tests para el endpoint GET /api/alumnos/me/materias/."""

    def setUp(self):
        self.client = APIClient()
        _install_jwt_mock(self)
        self.patcher_auth = self.patcher
        self.mock_validate.return_value = AuthenticatedUser(
            user_id=50,
            email="alumno50@correo.buap.mx",
            rol="alumno",
            nombre="Juan Perez",
        )

    def tearDown(self):
        self.patcher_auth.stop()

    @patch("apps.core.views.get_materia_detail")
    def test_get_my_materias_enriquecido(self, mock_get_materia_detail):
        """Alumno autenticado obtiene sus materias activas enriquecidas con MS-2."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token_alumno")

        mock_get_materia_detail.return_value = {
            "id": 123,
            "nrc": "11111",
            "nombre": "Matematicas Basicas",
            "seccion": "001",
            "clave": "MAT101",
            "docente_nombre": "Docente Uno",
            "docente_id": 888,
            "horario": "L-M 08:00",
            "periodo_id": 2026,
            "periodo_nombre": "Primavera 2026",
        }

        # 1. Crear el Alumno en la BD
        alumno = Alumno.objects.create(
            usuario_id=50,
            matricula="202050000",
            nombre="Juan",
            apellido="Perez",
            email="alumno50@correo.buap.mx",
            carrera="ICC",
            semestre=5
        )
        
        # 2. Crear InscripcionMateria activa
        InscripcionMateria.objects.create(
            alumno=alumno,
            materia_id=123,
            nrc="11111",
            nombre_materia="Matematicas",
            docente_nombre="Docente Uno",
            horario="L-M 08:00",
            activa=True
        )

        # 3. Hacer la peticion GET
        response = self.client.get("/api/alumnos/me/materias/")
        self.assertEqual(response.status_code, 200)
        
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(len(body["data"]["results"]), 1)
        self.assertEqual(body["data"]["results"][0]["materia_id"], 123)
        self.assertEqual(body["data"]["results"][0]["materia_detail"]["clave"], "MAT101")
        self.assertEqual(body["data"]["results"][0]["materia_detail"]["periodo_nombre"], "Primavera 2026")

    def test_get_my_materias_sin_inscripciones(self):
        """Alumno con cero inscripciones obtiene una lista vacia (200)."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token_alumno")
        
        # Crear el Alumno en la BD, sin inscripciones
        Alumno.objects.create(
            usuario_id=50,
            matricula="202050000",
            nombre="Juan",
            apellido="Perez",
            email="alumno50@correo.buap.mx",
            carrera="ICC",
            semestre=5
        )
        
        response = self.client.get("/api/alumnos/me/materias/")
        self.assertEqual(response.status_code, 200)
        
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(len(body["data"]["results"]), 0)

    def test_get_my_materias_sin_alumno_asociado(self):
        """Usuario autenticado sin registro de alumno retorna 404."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token_alumno")

        response = self.client.get("/api/alumnos/me/materias/")
        self.assertEqual(response.status_code, 404)

        body = response.json()
        self.assertFalse(body["success"])
        self.assertIn("registro de alumno", body["message"].lower())

    def test_get_my_materias_vincula_por_email(self):
        """Si usuario_id no esta en alumno pero el email coincide, vincula y lista materias."""
        self.mock_validate.return_value = AuthenticatedUser(
            user_id=312,
            email="202228369@alumno.buap.mx",
            rol="alumno",
            nombre="EVER Z. LOPEZ RAMIREZ",
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token_alumno")

        alumno = Alumno.objects.create(
            usuario_id=None,
            matricula="202228369",
            nombre="EVER Z.",
            apellido="LOPEZ RAMIREZ",
            email="202228369@alumno.buap.mx",
            carrera="ICC",
            semestre=5,
        )
        InscripcionMateria.objects.create(
            alumno=alumno,
            materia_id=64,
            nrc="50130",
            nombre_materia="Servicios Web",
            docente_nombre="Docente Demo",
            horario="L-M 08:00",
            activa=True,
        )

        response = self.client.get("/api/alumnos/me/materias/")
        self.assertEqual(response.status_code, 200)

        alumno.refresh_from_db()
        self.assertEqual(alumno.usuario_id, 312)

        body = response.json()
        self.assertEqual(len(body["data"]["results"]), 1)
        self.assertEqual(body["data"]["results"][0]["materia_id"], 64)


class PasswordFromEmailTests(TestCase):
    def test_local_part_before_at(self):
        from apps.core.services.identity import password_from_email

        self.assertEqual(
            password_from_email("maria.garcia@correo.buap.mx"),
            "maria.garcia",
        )
        self.assertEqual(password_from_email("david@correo.buap.mx"), "david")

    def test_strips_whitespace(self):
        from apps.core.services.identity import password_from_email

        self.assertEqual(
            password_from_email("  ana.lopez@correo.buap.mx  "),
            "ana.lopez",
        )


