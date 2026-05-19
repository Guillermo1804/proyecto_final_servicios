from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.exceptions import ParseError

from apps.core.models import Periodo, Materia
from apps.core.serializers import PeriodoSerializer, MateriaSerializer
from utils.pagination import AGMPagination
from utils.responses import error_response, success_response
from utils.auth import jwt_required


class PeriodoViewSet(ViewSet):
    """
    ViewSet para CRUD de Periodos académicos.
    Incluye acción custom `activar` con transacción atómica + select_for_update.
    Auth se inyectará vía @jwt_required cuando MS-1 esté operativo.
    """
    pagination_class = AGMPagination

    # ── LIST ────────────────────────────────────────────────────────────
    @jwt_required()
    def list(self, request):
        qs = Periodo.objects.all().order_by("-fecha_creacion")
        paginator = AGMPagination()
        page = paginator.paginate_queryset(qs, request)
        data = PeriodoSerializer(page, many=True).data
        return Response(paginator.get_paginated_envelope(data))

    # ── RETRIEVE ────────────────────────────────────────────────────────
    @jwt_required()
    def retrieve(self, request, pk=None):
        try:
            periodo = Periodo.objects.get(pk=pk)
        except Periodo.DoesNotExist:
            return error_response("Periodo no encontrado", status=404)
        return success_response(PeriodoSerializer(periodo).data)

    # ── CREATE ──────────────────────────────────────────────────────────
    @jwt_required(roles=["admin"])
    def create(self, request):
        serializer = PeriodoSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Datos inválidos", errors=serializer.errors, status=400
            )
        periodo = serializer.save()
        return success_response(
            PeriodoSerializer(periodo).data,
            message="Periodo creado exitosamente",
            status=201,
        )

    # ── UPDATE ──────────────────────────────────────────────────────────
    @jwt_required(roles=["admin"])
    def update(self, request, pk=None):
        try:
            periodo = Periodo.objects.get(pk=pk)
        except Periodo.DoesNotExist:
            return error_response("Periodo no encontrado", status=404)
        serializer = PeriodoSerializer(periodo, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                "Datos inválidos", errors=serializer.errors, status=400
            )
        periodo = serializer.save()
        return success_response(
            PeriodoSerializer(periodo).data,
            message="Periodo actualizado exitosamente",
        )

    # ── DESTROY ─────────────────────────────────────────────────────────
    @jwt_required(roles=["admin"])
    def destroy(self, request, pk=None):
        try:
            periodo = Periodo.objects.get(pk=pk)
        except Periodo.DoesNotExist:
            return error_response("Periodo no encontrado", status=404)
        if periodo.materias.exists():
            return error_response(
                "No se puede eliminar un periodo con materias asociadas",
                status=400,
            )
        periodo.delete()
        return success_response(None, message="Periodo eliminado exitosamente")

    # ── ACTIVAR (custom action) ─────────────────────────────────────────
    @jwt_required(roles=["admin"])
    @action(detail=True, methods=["post"], url_path="activar")
    def activar(self, request, pk=None):
        """
        Activa un periodo y desactiva cualquier otro activo.
        Usa select_for_update() + transaction.atomic() para garantizar
        que solo un periodo esté activo a la vez.
        """
        try:
            with transaction.atomic():
                # Bloquear el periodo objetivo
                periodo = Periodo.objects.select_for_update().get(pk=pk)
                # Desactivar cualquier otro periodo activo
                Periodo.objects.filter(activo=True).exclude(pk=pk).update(
                    activo=False
                )
                # Activar el periodo indicado
                periodo.activo = True
                periodo.save(update_fields=["activo", "fecha_actualizacion"])
        except Periodo.DoesNotExist:
            return error_response("Periodo no encontrado", status=404)
        except IntegrityError:
            return error_response(
                "Error de integridad al activar el periodo", status=400
            )
        return success_response(
            PeriodoSerializer(periodo).data,
            message="Periodo activado exitosamente",
        )

    # ── ACTIVO (get currently active) ───────────────────────────────────
    @action(detail=False, methods=["get"], url_path="activo")
    def activo(self, request):
        """Retorna el periodo actualmente activo."""
        try:
            periodo = Periodo.objects.get(activo=True)
        except Periodo.DoesNotExist:
            return error_response("No hay periodo activo", status=404)
        return success_response(PeriodoSerializer(periodo).data)

    # ── IMPORTAR MATERIAS (custom action) ───────────────────────────────
    @jwt_required(roles=["admin"])
    @action(detail=True, methods=["post"], url_path="importar-materias")
    def importar_materias(self, request, pk=None):
        """
        Recibe un archivo PDF y usa pdfplumber para extraer materias y 
        hacer un upsert (crear/actualizar) por NRC dentro de este periodo.
        """
        try:
            periodo = Periodo.objects.get(pk=pk)
        except Periodo.DoesNotExist:
            return error_response("Periodo no encontrado", status=404)

        archivo = request.FILES.get("archivo")
        if not archivo:
            return error_response("Archivo PDF no proporcionado", status=400)

        if not archivo.name.lower().endswith(".pdf"):
            return error_response("El archivo debe ser un PDF", status=400)

        from utils.pdf_parser import parsear_pdf_materias
        try:
            materias_parseadas, errores_count = parsear_pdf_materias(archivo)
        except ValueError as e:
            return error_response(str(e), status=400)
        except Exception as e:
            return error_response("Error interno al procesar PDF", status=500)

        creadas = 0
        actualizadas = 0

        try:
            from apps.core.models import Materia
            with transaction.atomic():
                for mat in materias_parseadas:
                    materia, created = Materia.objects.update_or_create(
                        periodo=periodo,
                        nrc=mat["nrc"],
                        defaults={
                            "clave": mat["clave"],
                            "nombre": mat["nombre"],
                            "seccion": mat["seccion"],
                            "docente_nombre": mat["docente_nombre"],
                            "horario": mat["horario"],
                        }
                    )
                    if created:
                        creadas += 1
                    else:
                        actualizadas += 1
        except Exception as e:
            return error_response(f"Error de BD durante el import: {str(e)}", status=500)

        return success_response({
            "creadas": creadas,
            "actualizadas": actualizadas,
            "errores": errores_count
        }, message="Materias importadas exitosamente")


class MateriaViewSet(ModelViewSet):
    """
    ViewSet para CRUD de Materias.
    Incluye filtrado por periodo_id, nrc, nombre, docente_nombre.
    """
    queryset = Materia.objects.all().order_by("-fecha_creacion")
    serializer_class = MateriaSerializer
    pagination_class = AGMPagination

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        
        allowed_params = {"periodo_id", "nrc", "nombre", "docente_nombre", "page", "limit"}
        # Quitamos la validación estricta de aquí porque raise ParseError rompe el envelope.
        # Lo haremos en list().

        periodo_id = params.get("periodo_id")
        if periodo_id:
            qs = qs.filter(periodo_id=periodo_id)
            
        nrc = params.get("nrc")
        if nrc:
            qs = qs.filter(nrc=nrc)
            
        nombre = params.get("nombre")
        if nombre:
            qs = qs.filter(nombre__icontains=nombre)
            
        docente_nombre = params.get("docente_nombre")
        if docente_nombre:
            qs = qs.filter(docente_nombre__icontains=docente_nombre)
            
        return qs

    @jwt_required()
    def list(self, request, *args, **kwargs):
        params = request.query_params
        allowed_params = {"periodo_id", "nrc", "nombre", "docente_nombre", "page", "limit"}
        for p in params:
            if p not in allowed_params:
                return error_response(f"Parámetro no reconocido: {p}", status=400)
        
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    @jwt_required()
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    @jwt_required(roles=["admin"])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Datos inválidos", errors=serializer.errors, status=400)
        serializer.save()
        return success_response(serializer.data, message="Materia creada exitosamente", status=201)

    @jwt_required(roles=["admin"])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return error_response("Datos inválidos", errors=serializer.errors, status=400)
        serializer.save()
        return success_response(serializer.data, message="Materia actualizada exitosamente")

    @jwt_required(roles=["admin"])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Validación de alumnos inscritos vía MS-3 en el futuro
        instance.delete()
        return success_response(None, message="Materia eliminada exitosamente")

