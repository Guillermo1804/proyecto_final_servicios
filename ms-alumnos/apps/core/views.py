import logging
import os
import tempfile

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action

from apps.core.models import Alumno, Docente, InscripcionMateria
from apps.core.serializers import AlumnoSerializer, DocenteSerializer, InscripcionMateriaSerializer
from apps.core.services.alumno_import import process_alumno_import_batch
from apps.core.services.docente_import import process_docente_import_rows
from apps.core.services.materia_context import resolve_materia_context
from apps.core.event_bus.publishers import publish_alumno_withdrawn
from utils.auth import jwt_required
from utils.excel_parser import parse_alumnos_file
from utils.notificaciones_client import send_baja_notif
from utils.pagination import AGMPagination
from utils.pdf_docentes_parser import parse_pdf_docentes
from utils.periodos_client import get_materia_docente_id
from utils.periodos_ms2_client import get_materia_detail
from utils.responses import error_response, success_response

logger = logging.getLogger(__name__)


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

        return queryset

    @jwt_required()
    def list(self, request, *args, **kwargs):
        params = request.query_params
        allowed_params = {"page", "limit", "nombre", "apellido", "departamento", "usuario_id"}
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


class AlumnoViewSet(viewsets.ModelViewSet):
    """ViewSet para CRUD e Importación de Alumnos."""

    queryset = Alumno.objects.all().order_by("-fecha_creacion")
    serializer_class = AlumnoSerializer
    pagination_class = AGMPagination

    @jwt_required(roles=["admin"])
    @action(detail=False, methods=["post"], url_path="importar/preview")
    def importar_preview(self, request):
        archivo = request.FILES.get("archivo")
        if not archivo:
            return error_response(
                "No se proporcionó ningún archivo ('archivo' multipart esperado).",
                status=400,
            )

        validas, errores = parse_alumnos_file(archivo, archivo.name)
        return success_response(
            {
                "validas": validas,
                "errores": errores,
                "total_validas": len(validas),
                "total_errores": len(errores),
            }
        )

    @jwt_required(roles=["admin"])
    @action(detail=False, methods=["post"], url_path="importar/confirmar")
    def importar_confirmar(self, request):
        alumnos_data = request.data.get("alumnos", [])
        if not alumnos_data:
            return error_response(
                "No se proporcionaron datos de alumnos (JSON con lista 'alumnos' esperado).",
                status=400,
            )

        try:
            creados, actualizados = process_alumno_import_batch(alumnos_data)
            return success_response(
                {"creados": creados, "actualizados": actualizados},
                message="Importación completada con éxito.",
            )
        except Exception as e:
            logger.exception("importar_confirmar failed")
            return error_response(f"Error durante la persistencia de datos: {e}", status=500)

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

    @jwt_required()
    @action(detail=False, methods=["get"], url_path="me/materias")
    def me_materias(self, request):
        user_id = request.user_id
        try:
            alumno = Alumno.objects.get(usuario_id=user_id)
        except Alumno.DoesNotExist:
            return error_response("El alumno asociado al usuario no existe.", status=404)

        queryset = InscripcionMateria.objects.filter(alumno=alumno, activa=True).order_by(
            "id"
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = InscripcionMateriaSerializer(page, many=True)
            data = serializer.data
            for item in data:
                item["materia_detail"] = get_materia_detail(item["materia_id"])
            return self.get_paginated_response(data)

        serializer = InscripcionMateriaSerializer(queryset, many=True)
        data = serializer.data
        for item in data:
            item["materia_detail"] = get_materia_detail(item["materia_id"])
        return success_response(data)
