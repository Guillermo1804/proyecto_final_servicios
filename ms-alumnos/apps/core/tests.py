import os

import grpc
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from unittest.mock import MagicMock, patch
from rest_framework.test import APIClient
from apps.core.models import Alumno, Docente, InscripcionMateria
from proto_generated import alumnos_pb2, alumnos_pb2_grpc, auth_pb2
from grpc_server.servicer import AlumnosServicer

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
        self.patcher = patch("utils.auth.get_auth_stub")
        self.mock_get_auth_stub = self.patcher.start()
        
        self.mock_stub = MagicMock()
        self.mock_stub.ValidateToken.return_value = auth_pb2.ValidateTokenResponse(
            valid=True, user_id=1, email="test@buap.mx", rol="admin", nombre="Test"
        )
        self.mock_get_auth_stub.return_value = self.mock_stub

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
        self.mock_stub.ValidateToken.return_value = auth_pb2.ValidateTokenResponse(
            valid=True, user_id=2, email="alumno@buap.mx", rol="alumno", nombre="Test"
        )
        response = self.client.post("/api/docentes/", data={}, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])


class AlumnoImportTests(TestCase):
    """Tests para los flujos de importación de alumnos (Preview + Confirmar)."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        self.patcher = patch("utils.auth.get_auth_stub")
        self.mock_get_auth_stub = self.patcher.start()
        
        self.mock_stub = MagicMock()
        self.mock_stub.ValidateToken.return_value = auth_pb2.ValidateTokenResponse(
            valid=True, user_id=1, email="test@buap.mx", rol="admin", nombre="Test"
        )
        self.mock_get_auth_stub.return_value = self.mock_stub

    def tearDown(self):
        self.patcher.stop()

    def test_import_preview_csv_valido(self):
        """Verifica que un CSV se parsee correctamente en el preview."""
        csv_content = "matricula,nombre,paterno,materno,email,carrera,semestre\n202012345,Juan,Perez,Lopez,juan@alumno.buap.mx,ICC,3"
        csv_file = SimpleUploadedFile("alumnos.csv", csv_content.encode('utf-8'), content_type="text/csv")
        
        response = self.client.post("/api/alumnos/importar/preview/", {"archivo": csv_file}, format='multipart')
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["total_validas"], 1)
        self.assertEqual(data["validas"][0]["matricula"], "202012345")
        self.assertEqual(data["validas"][0]["apellido"], "Perez Lopez")

    @patch("apps.core.views.send_bienvenida")
    def test_import_confirmar_upsert(self, mock_send):
        """Verifica que el upsert cree registros y llame a la notificación."""
        mock_send.return_value = True
        
        alumnos_data = {
            "alumnos": [
                {
                    "matricula": "202099999",
                    "nombre": "Test",
                    "apellido": "Import",
                    "email": "test@buap.mx",
                    "carrera": "ICC",
                    "semestre": 1
                }
            ]
        }
        
        response = self.client.post("/api/alumnos/importar/confirmar/", alumnos_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["creados"], 1)
        self.assertTrue(Alumno.objects.filter(matricula="202099999").exists())
        self.assertEqual(mock_send.call_count, 1)

    @patch("apps.core.views.send_bienvenida")
    def test_import_confirmar_fallo_notificacion_no_aborta(self, mock_send):
        """Si falla gRPC, el import debe continuar (graceful failure)."""
        mock_send.return_value = False # Simula fallo de red/timeout
        
        alumnos_data = {
            "alumnos": [
                {
                    "matricula": "202088888",
                    "nombre": "Graceful",
                    "apellido": "Failure",
                    "email": "fail@buap.mx"
                }
            ]
        }
        
        response = self.client.post("/api/alumnos/importar/confirmar/", alumnos_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["creados"], 1)
        self.assertTrue(Alumno.objects.filter(matricula="202088888").exists())


class AlumnoPorMateriaTests(TestCase):
    """Tests para el endpoint /api/alumnos/por-materia/."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        self.patcher = patch("utils.auth.get_auth_stub")
        self.mock_get_auth_stub = self.patcher.start()
        
        self.mock_stub = MagicMock()
        self.mock_stub.ValidateToken.return_value = auth_pb2.ValidateTokenResponse(
            valid=True, user_id=1, email="test@buap.mx", rol="admin", nombre="Test"
        )
        self.mock_get_auth_stub.return_value = self.mock_stub

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

    @patch("apps.core.views.get_materia_docente_id", return_value=10)
    def test_por_materia_docente_titular_ok(self, _mock_titular):
        """Docente titular (usuario_id = docente_id MS-2) puede listar."""
        self.mock_stub.ValidateToken.return_value = auth_pb2.ValidateTokenResponse(
            valid=True, user_id=10, email="doc@buap.mx", rol="docente", nombre="Doc"
        )
        response = self.client.get("/api/alumnos/por-materia/?materia_id=1")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    @patch("apps.core.views.get_materia_docente_id", return_value=99)
    def test_por_materia_docente_no_titular_403(self, _mock_titular):
        """Docente que no es titular recibe 403."""
        self.mock_stub.ValidateToken.return_value = auth_pb2.ValidateTokenResponse(
            valid=True, user_id=5, email="otro@buap.mx", rol="docente", nombre="Otro"
        )
        response = self.client.get("/api/alumnos/por-materia/?materia_id=1")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])


class AlumnoBajaMateriaTests(TestCase):
    """Tests para la baja irreversible de materias."""

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer valid_token")
        self.patcher = patch("utils.auth.get_auth_stub")
        self.mock_get_auth_stub = self.patcher.start()
        
        self.mock_stub = MagicMock()
        self.mock_stub.ValidateToken.return_value = auth_pb2.ValidateTokenResponse(
            valid=True, user_id=1, email="test@buap.mx", rol="admin", nombre="Test"
        )
        self.mock_get_auth_stub.return_value = self.mock_stub

        self.alumno = Alumno.objects.create(usuario_id=10, matricula="2020555", nombre="Luis", apellido="Baja", email="luis@b.com")
        self.insc = InscripcionMateria.objects.create(
            alumno=self.alumno, materia_id=5, nrc="500", nombre_materia="Bajas", docente_nombre="D5", activa=True
        )

    def tearDown(self):
        self.patcher.stop()

    @patch("apps.core.views.get_materia_docente_id", return_value=99)
    @patch("apps.core.views.send_baja_notif")
    def test_baja_materia_exitosa(self, mock_send, _mock_docente):
        """POST /api/alumnos/{id}/baja-materia/ marca activa=False y setea fecha_baja."""
        mock_send.return_value = True
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
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.kwargs["docente_id"], 99)

    @patch("apps.core.views.send_baja_notif")
    def test_baja_materia_ya_inactiva_falla(self, mock_send):
        """Intentar dar de baja una materia ya inactiva retorna 400."""
        self.insc.activa = False
        self.insc.save()
        
        payload = {"materia_id": 5}
        response = self.client.post(f"/api/alumnos/{self.alumno.id}/baja-materia/", payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "baja ya procesada")


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
    def test_target_from_env(self):
        from utils.notificaciones_client import _notificaciones_target

        self.assertEqual(_notificaciones_target(), 'ms-notificaciones:50056')


from django.core.files.uploadedfile import SimpleUploadedFile

class DocenteImportTests(TestCase):
    """Tests para el endpoint de importación de docentes POST /api/docentes/importar/."""

    def setUp(self):
        self.client = APIClient()
        self.patcher_auth = patch("utils.auth.get_auth_stub")
        self.mock_get_auth_stub = self.patcher_auth.start()
        
        self.mock_stub = MagicMock()
        self.mock_stub.ValidateToken.return_value = auth_pb2.ValidateTokenResponse(
            valid=True, user_id=1, email="admin@buap.mx", rol="admin", nombre="Admin"
        )
        self.mock_get_auth_stub.return_value = self.mock_stub

    def tearDown(self):
        self.patcher_auth.stop()

    @patch("apps.core.views.parse_pdf_docentes")
    @patch("apps.core.views.create_user_in_auth")
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

    @patch("apps.core.views.parse_pdf_docentes")
    @patch("apps.core.views.create_user_in_auth")
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
        self.patcher_auth = patch("utils.auth.get_auth_stub")
        self.mock_get_auth_stub = self.patcher_auth.start()
        
        self.mock_auth_stub = MagicMock()
        # Mocking ValidateToken for alumno (rol="alumno", user_id=50)
        self.mock_auth_stub.ValidateToken.return_value = auth_pb2.ValidateTokenResponse(
            valid=True, user_id=50, email="alumno50@correo.buap.mx", rol="alumno", nombre="Juan Perez"
        )
        self.mock_get_auth_stub.return_value = self.mock_auth_stub

    def tearDown(self):
        self.patcher_auth.stop()

    @patch("utils.periodos_ms2_client.get_periodos_stub")
    def test_get_my_materias_enriquecido(self, mock_get_periodos_stub):
        """Alumno autenticado obtiene sus materias activas enriquecidas con MS-2."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token_alumno")
        
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

        # 3. Mockear gRPC PeriodosService stub
        mock_periodos_stub = MagicMock()
        mock_periodos_stub.GetMateriaById.return_value = periodos_pb2.MateriaInfo(
            id=123,
            nrc="11111",
            nombre="Matematicas Basicas",
            seccion="001",
            clave="MAT101",
            docente_nombre="Docente Uno",
            docente_id=888,
            horario="L-M 08:00",
            periodo_id=2026,
            periodo_nombre="Primavera 2026"
        )
        mock_get_periodos_stub.return_value = mock_periodos_stub

        # 4. Hacer la peticion GET
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
        """Usuario autenticado cuyo usuario_id no tiene Alumno asociado retorna 404."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token_alumno")
        
        # No creamos Alumno en la BD para usuario_id=50
        response = self.client.get("/api/alumnos/me/materias/")
        self.assertEqual(response.status_code, 404)
        
        body = response.json()
        self.assertFalse(body["success"])
        self.assertIn("asociado al usuario no existe", body["message"])



