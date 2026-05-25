import logging
import os
import tempfile

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action

from apps.core.models import Alumno, Docente, InscripcionMateria
from apps.core.serializers import AlumnoSerializer, DocenteSerializer, InscripcionMateriaSerializer
from apps.core.services.alumno_identity import resolve_alumno_for_request
from apps.core.services.alumno_import import process_alumno_import_batch
from apps.core.services.alumno_import_preview import build_alumno_import_preview
from apps.core.services.docente_import import process_docente_import_rows
from utils.pdf_alumnos_parser import parse_pdf_alumnos
from apps.core.services.alumno_provision import deprovision_alumno_usuario, provision_alumno_usuario
from apps.core.services.docente_provision import provision_docente_usuario
from apps.core.services.materia_context import resolve_materia_context
from apps.core.event_bus.publishers import publish_alumno_withdrawn
from utils.auth import jwt_required
from utils.notificaciones_client import send_baja_notif
from utils.pagination import AGMPagination
from utils.pdf_docentes_parser import parse_pdf_docentes
from utils.periodos_client import get_materia_docente_id
from utils.periodos_ms2_client import get_materia_detail
from utils.responses import error_response, success_response

logger = logging.getLogger(__name__)


def _parse_pdf_alumnos_upload(pdf_file, materia_id: int) -> tuple[list, list, dict, list, str]:
    """
    Guarda PDF temporal, parsea filas y valida NRC vs materia.
    Retorna (rows, parse_errors, meta, errores, temp_file_path).
    """
    temp_dir = os.path.join(settings.BASE_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    rows: list = []
    parse_errors: list = []
    meta: dict = {}
    errores: list = []

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=temp_dir) as temp_file:
        for chunk in pdf_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name

    try:
        rows, parse_errors, meta = parse_pdf_alumnos(temp_file_path)
        for pe in parse_errors:
            errores.append({"error": pe})

        materia_ctx = resolve_materia_context(materia_id)
        pdf_nrc = (meta.get("nrc") or "").strip()
        if pdf_nrc and materia_ctx.get("nrc") and pdf_nrc != materia_ctx["nrc"]:
            errores.append(
                {
                    "error": (
                        f"NRC del PDF ({pdf_nrc}) no coincide con la materia "
                        f"({materia_ctx['nrc']}). Revise que subio el PDF correcto."
                    )
                }
            )
    except Exception:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise

    return rows, parse_errors, meta, errores, temp_file_path


def _enrich_inscripcion_item(item: dict) -> dict:
    """Completa NRC/nombre/horario desde MS-2 si la inscripcion local esta incompleta."""
    detail = item.get("materia_detail")
    if not detail:
        detail = get_materia_detail(int(item.get("materia_id") or 0))
    if detail:
        item["materia_detail"] = detail
        if not (item.get("nrc") or "").strip():
            item["nrc"] = detail.get("nrc") or ""
        if not (item.get("nombre_materia") or "").strip():
            item["nombre_materia"] = detail.get("nombre") or ""
        if not (item.get("docente_nombre") or "").strip():
            item["docente_nombre"] = detail.get("docente_nombre") or ""
        if not (item.get("horario") or "").strip():
            item["horario"] = detail.get("horario") or ""
    return item


def _use_event_bus() -> bool:
    return bool(getattr(settings, "USE_EVENT_BUS", False))


class DocenteViewSet(viewsets.ModelViewSet):
    """ViewSet para CRUD de Docentes con filtrado y paginación."""

    queryset = Docente.objects.all().order_by("-fecha_creacion")
    serializer_class = DocenteSerializer
    pagination_class = AGMPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        nombre = params.get("nombre")
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)

        apellido = params.get("apellido")
        if apellido:
            queryset = queryset.filter(apellido__icontains=apellido)

        departamento = params.get("departamento")
        if departamento:
            queryset = queryset.filter(departamento__icontains=departamento)

        usuario_id = params.get("usuario_id")
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)

        buscar = (params.get("buscar") or "").strip()
        if buscar:
            for token in buscar.split():
                queryset = queryset.filter(
                    Q(nombre__icontains=token)
                    | Q(apellido__icontains=token)
                    | Q(email__icontains=token)
                    | Q(departamento__icontains=token)
                )

        return queryset

    @jwt_required()
    def list(self, request, *args, **kwargs):
        params = request.query_params
        allowed_params = {
            "page",
            "limit",
            "nombre",
            "apellido",
            "departamento",
            "usuario_id",
            "buscar",
        }
        unrecognized = set(params.keys()) - allowed_params
        if unrecognized:
            return error_response(
                message=f"Parámetros no reconocidos: {', '.join(unrecognized)}",
                status=400,
            )
        return super().list(request, *args, **kwargs)

    @jwt_required(roles=["admin"])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usuario_id = request.data.get("usuario_id")
        if not usuario_id:
            return error_response(
                "El campo usuario_id es requerido para crear un docente.",
                status=400,
            )

        instance = serializer.save(usuario_id=usuario_id)
        return success_response(
            data=DocenteSerializer(instance).data,
            message="Docente creado exitosamente",
            status=status.HTTP_201_CREATED,
        )

    @jwt_required()
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    @jwt_required(roles=["admin"])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(serializer.data, message="Docente actualizado")

    @jwt_required(roles=["admin"])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(None, message="Docente eliminado", status=status.HTTP_200_OK)

    @jwt_required(roles=["admin"])
    @action(detail=False, methods=["post"], url_path="importar")
    def importar(self, request):
        pdf_file = request.FILES.get("file")
        if not pdf_file:
            return error_response("El archivo 'file' es requerido.", status=400)

        if not pdf_file.name.endswith(".pdf"):
            return error_response("El archivo debe ser un PDF válido.", status=400)

        temp_dir = os.path.join(settings.BASE_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=temp_dir) as temp_file:
            for chunk in pdf_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        creados = 0
        omitidos = 0
        errores = []

        try:
            rows, parse_errors = parse_pdf_docentes(temp_file_path)
            for pe in parse_errors:
                errores.append({"error": pe})

            creados, omitidos, row_errors = process_docente_import_rows(rows)
            errores.extend(row_errors)
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        filas_leidas = len(rows)
        summary = {
            "creados": creados,
            "omitidos": omitidos,
            "errores": len(errores),
            "filas_leidas": filas_leidas,
            "errores_parseo": len(parse_errors),
        }
        if errores:
            summary["detalle_errores"] = errores[:20]
        msg = "Importación de docentes completada"
        if filas_leidas == 0 and creados == 0:
            msg = (
                "PDF procesado pero no se encontraron filas validas de docentes. "
                "Revise detalle_errores."
            )
        return success_response(summary, message=msg)

    @jwt_required(roles=["admin"])
    @action(detail=True, methods=["post"], url_path="activar-usuario")
    def activar_usuario(self, request, pk=None):
        """Crea o vincula usuario MS-1 para un docente Inactivo (sin usuario_id)."""
        docente = self.get_object()
        if docente.usuario_id:
            serializer = DocenteSerializer(docente)
            return success_response(
                serializer.data,
                message="El docente ya tiene usuario activo en MS-1.",
            )

        docente, err = provision_docente_usuario(docente)
        if err:
            return error_response(err, status=400)

        serializer = DocenteSerializer(docente)
        return success_response(
            serializer.data,
            message="Usuario de docente activado. Puede iniciar sesion con su correo.",
        )


class AlumnoViewSet(viewsets.ModelViewSet):
    """ViewSet para CRUD e Importación de Alumnos."""

    queryset = Alumno.objects.all().order_by("-fecha_creacion")
    serializer_class = AlumnoSerializer
    pagination_class = AGMPagination

    @jwt_required(roles=["admin", "docente"])
    @action(detail=False, methods=["post"], url_path="importar/preview")
    def importar_preview(self, request):
        """Parsea PDF y devuelve vista previa sin guardar en BD."""
        pdf_file = request.FILES.get("file")
        if not pdf_file:
            return error_response("El archivo 'file' es requerido.", status=400)

        if not pdf_file.name.lower().endswith(".pdf"):
            return error_response("El archivo debe ser un PDF valido.", status=400)

        try:
            materia_id = int(request.data.get("materia_id") or request.query_params.get("materia_id") or 0)
        except (TypeError, ValueError):
            return error_response("materia_id debe ser un entero.", status=400)

        if materia_id <= 0:
            return error_response(
                "materia_id es obligatorio (ID de la materia en MS-2).",
                status=400,
            )

        temp_file_path = ""
        try:
            rows, parse_errors, meta, errores, temp_file_path = _parse_pdf_alumnos_upload(
                pdf_file, materia_id
            )
            preview_rows, resumen = build_alumno_import_preview(rows, materia_id)
        except Exception as exc:
            logger.exception("importar alumnos preview failed")
            return error_response(f"Error al generar vista previa: {exc}", status=500)
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        payload = {
            "filas": preview_rows,
            "resumen": resumen,
            "errores_parseo": len(parse_errors),
            "nrc_pdf": meta.get("nrc") or "",
            "nombre_materia_pdf": meta.get("nombre_materia") or "",
            "docente_pdf": meta.get("docente") or "",
            "periodo_pdf": meta.get("periodo") or "",
        }
        if errores:
            payload["advertencias"] = errores[:20]

        msg = "Vista previa generada"
        if not preview_rows:
            msg = (
                "PDF procesado pero no se encontraron filas validas de alumnos. "
                "Exporte la lista de clase desde Servicios Web (Ctrl+P)."
            )
        return success_response(payload, message=msg)

    @jwt_required(roles=["admin", "docente"])
    @action(detail=False, methods=["post"], url_path="importar/confirmar")
    def importar_confirmar(self, request):
        """Confirma importacion con filas devueltas por importar/preview."""
        try:
            materia_id = int(request.data.get("materia_id") or 0)
        except (TypeError, ValueError):
            return error_response("materia_id debe ser un entero.", status=400)

        if materia_id <= 0:
            return error_response(
                "materia_id es obligatorio (ID de la materia en MS-2).",
                status=400,
            )

        alumnos = request.data.get("alumnos")
        if not isinstance(alumnos, list) or not alumnos:
            return error_response(
                "alumnos es obligatorio (lista de filas de la vista previa).",
                status=400,
            )

        rows = []
        for item in alumnos:
            if not isinstance(item, dict):
                continue
            matricula = str(item.get("matricula") or "").strip()
            if not matricula:
                continue
            rows.append(
                {
                    "matricula": matricula,
                    "nombre": item.get("nombre") or "",
                    "apellido": item.get("apellido") or "",
                    "email": item.get("email") or "",
                    "carrera": item.get("carrera") or "",
                    "semestre": item.get("semestre") or 1,
                    "materia_id": materia_id,
                }
            )

        if not rows:
            return error_response("No hay filas validas para importar.", status=400)

        try:
            creados, actualizados, inscritos = process_alumno_import_batch(
                rows,
                materia_id=materia_id,
            )
        except Exception as exc:
            logger.exception("importar alumnos confirmar failed")
            return error_response(f"Error durante la importacion: {exc}", status=500)

        summary = {
            "creados": creados,
            "actualizados": actualizados,
            "inscritos": inscritos,
            "errores": 0,
            "filas_leidas": len(rows),
            "errores_parseo": 0,
        }
        return success_response(summary, message="Importacion de alumnos completada")

    @jwt_required(roles=["admin", "docente"])
    @action(detail=False, methods=["post"], url_path="importar")
    def importar(self, request):
        """
        Importa alumnos desde PDF lista de clase BUAP (mismo flujo que docentes/materias).
        Multipart: file (PDF), materia_id (obligatorio para inscribir en la materia).
        """
        pdf_file = request.FILES.get("file")
        if not pdf_file:
            return error_response("El archivo 'file' es requerido.", status=400)

        if not pdf_file.name.lower().endswith(".pdf"):
            return error_response("El archivo debe ser un PDF valido.", status=400)

        try:
            materia_id = int(request.data.get("materia_id") or request.query_params.get("materia_id") or 0)
        except (TypeError, ValueError):
            return error_response("materia_id debe ser un entero.", status=400)

        if materia_id <= 0:
            return error_response(
                "materia_id es obligatorio (ID de la materia en MS-2).",
                status=400,
            )

        temp_file_path = ""
        errores: list = []
        try:
            rows, parse_errors, meta, errores, temp_file_path = _parse_pdf_alumnos_upload(
                pdf_file, materia_id
            )

            for row in rows:
                row["materia_id"] = materia_id

            creados, actualizados, inscritos = process_alumno_import_batch(
                rows,
                materia_id=materia_id,
            )
        except Exception as exc:
            logger.exception("importar alumnos PDF failed")
            return error_response(f"Error durante la importacion: {exc}", status=500)
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        filas_leidas = len(rows)
        summary = {
            "creados": creados,
            "actualizados": actualizados,
            "inscritos": inscritos,
            "errores": len(errores),
            "filas_leidas": filas_leidas,
            "errores_parseo": len(parse_errors),
            "nrc_pdf": meta.get("nrc") or "",
            "nombre_materia_pdf": meta.get("nombre_materia") or "",
        }
        if errores:
            summary["detalle_errores"] = errores[:20]

        msg = "Importacion de alumnos completada"
        if filas_leidas == 0 and creados == 0:
            msg = (
                "PDF procesado pero no se encontraron filas validas de alumnos. "
                "Exporte la lista de clase desde Servicios Web (Ctrl+P)."
            )
        return success_response(summary, message=msg)

    @jwt_required()
    @action(detail=False, methods=["get"], url_path="por-materia")
    def por_materia(self, request):
        materia_id = request.query_params.get("materia_id")
        if not materia_id:
            return error_response("El parámetro 'materia_id' es requerido.", status=400)

        try:
            materia_id = int(materia_id)
        except ValueError:
            return error_response(
                "El parámetro 'materia_id' debe ser un número entero.",
                status=400,
            )

        queryset = (
            InscripcionMateria.objects.filter(materia_id=materia_id, activa=True)
            .select_related("alumno")
            .order_by("alumno__apellido", "alumno__nombre")
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = InscripcionMateriaSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = InscripcionMateriaSerializer(queryset, many=True)
        return success_response(serializer.data)

    @jwt_required(roles=["admin", "docente"])
    @action(detail=True, methods=["post"], url_path="activar-usuario")
    def activar_usuario(self, request, pk=None):
        """Crea o vincula usuario MS-1 para un alumno sin usuario_id."""
        alumno = self.get_object()
        if alumno.usuario_id:
            return success_response(
                AlumnoSerializer(alumno).data,
                message="El alumno ya tiene usuario activo en MS-1.",
            )

        alumno, err = provision_alumno_usuario(alumno)
        if err:
            return error_response(err, status=400)

        return success_response(
            AlumnoSerializer(alumno).data,
            message="Usuario de alumno activado en MS-1.",
        )

    @jwt_required(roles=["admin", "docente"])
    @action(detail=True, methods=["post"], url_path="desactivar-usuario")
    def desactivar_usuario(self, request, pk=None):
        """Desactiva usuario MS-1 y desvincula alumno.usuario_id."""
        alumno = self.get_object()
        if not alumno.usuario_id:
            return success_response(
                AlumnoSerializer(alumno).data,
                message="El alumno ya esta sin acceso en MS-1.",
            )

        alumno, err = deprovision_alumno_usuario(alumno)
        if err:
            return error_response(err, status=400)

        return success_response(
            AlumnoSerializer(alumno).data,
            message="Acceso del alumno desactivado en MS-1.",
        )

    @jwt_required(roles=["admin"])
    @action(detail=True, methods=["post"], url_path="baja-materia")
    def baja_materia(self, request, pk=None):
        alumno = self.get_object()
        materia_id = request.data.get("materia_id")

        if not materia_id:
            return error_response(
                "El campo 'materia_id' es requerido en el cuerpo JSON.",
                status=400,
            )

        try:
            with transaction.atomic():
                inscripcion = (
                    InscripcionMateria.objects.select_for_update()
                    .filter(alumno=alumno, materia_id=materia_id)
                    .first()
                )

                if not inscripcion:
                    return error_response(
                        "No se encontró una inscripción para esta materia.",
                        status=404,
                    )

                if not inscripcion.activa:
                    return error_response("baja ya procesada", status=400)

                inscripcion.activa = False
                inscripcion.fecha_baja = timezone.now()
                inscripcion.save()

                materia_ctx = resolve_materia_context(int(materia_id))
                docente_id = materia_ctx.get("docente_id") or get_materia_docente_id(
                    int(materia_id)
                ) or 0

                if _use_event_bus():
                    publish_alumno_withdrawn(
                        inscripcion,
                        periodo_id=materia_ctx["periodo_id"],
                        docente_email=materia_ctx["docente_email"],
                        docente_id=int(docente_id or 0),
                    )
                else:
                    send_baja_notif(inscripcion, docente_id=int(docente_id or 0))

            return success_response(
                {
                    "alumno": alumno.matricula,
                    "materia_id": materia_id,
                    "fecha_baja": inscripcion.fecha_baja,
                },
                message="Baja de materia procesada exitosamente.",
            )

        except Exception as e:
            logger.exception("baja_materia failed")
            return error_response(f"Error inesperado al procesar la baja: {e}", status=500)

    @jwt_required(roles=["alumno", "admin"])
    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Perfil del alumno autenticado (vincula usuario_id por email si hace falta)."""
        alumno = resolve_alumno_for_request(request)
        if not alumno:
            return error_response(
                "No hay registro de alumno vinculado a tu cuenta. "
                "Pide al docente que te importe en la lista de clase.",
                status=404,
            )
        return success_response(AlumnoSerializer(alumno).data)

    @jwt_required(roles=["alumno", "admin"])
    @action(detail=False, methods=["get"], url_path="me/materias")
    def me_materias(self, request):
        alumno = resolve_alumno_for_request(request)
        if not alumno:
            return error_response(
                "No hay registro de alumno vinculado a tu cuenta. "
                "Pide al docente que te importe en la lista de clase.",
                status=404,
            )

        queryset = InscripcionMateria.objects.filter(alumno=alumno, activa=True).order_by(
            "id"
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = InscripcionMateriaSerializer(page, many=True)
            data = [_enrich_inscripcion_item(dict(item)) for item in serializer.data]
            return self.get_paginated_response(data)

        serializer = InscripcionMateriaSerializer(queryset, many=True)
        data = [_enrich_inscripcion_item(dict(item)) for item in serializer.data]
        return success_response({"count": len(data), "results": data})
