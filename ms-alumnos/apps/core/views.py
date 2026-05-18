import logging

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import uuid
import tempfile
import os
from django.conf import settings
from apps.core.models import Alumno, Docente, InscripcionMateria
from apps.core.serializers import AlumnoSerializer, DocenteSerializer, InscripcionMateriaSerializer
from utils.auth_client import create_user_alumno
from utils.excel_parser import parse_alumnos_file
from utils.pagination import AGMPagination
from utils.notificaciones_client import send_baja_notif, send_bienvenida
from utils.periodos_client import get_materia_docente_id
from utils.responses import error_response, success_response
from utils.auth import jwt_required
from utils.pdf_docentes_parser import parse_pdf_docentes
from utils.auth_ms1_client import create_user_in_auth

logger = logging.getLogger(__name__)


class DocenteViewSet(viewsets.ModelViewSet):
    """ViewSet para CRUD de Docentes con filtrado y paginación."""
    queryset = Docente.objects.all().order_by("-fecha_creacion")
    serializer_class = DocenteSerializer
    pagination_class = AGMPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        
        # El filtrado real se hace en list() para validar parámetros extra,
        # pero aquí aplicamos los filtros válidos.
        
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
                status=400
            )
        return super().list(request, *args, **kwargs)

    @jwt_required(roles=["admin"])
    def create(self, request, *args, **kwargs):
        """Crear un docente. Se permite pasar usuario_id manualmente para este issue."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extraemos usuario_id del request data ya que es read_only en el serializer
        usuario_id = request.data.get("usuario_id")
        if not usuario_id:
            return error_response("El campo usuario_id es requerido para crear un docente.", status=400)
            
        instance = serializer.save(usuario_id=usuario_id)
        return success_response(
            data=DocenteSerializer(instance).data,
            message="Docente creado exitosamente",
            status=status.HTTP_201_CREATED
        )

    @jwt_required()
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    @jwt_required(roles=["admin"])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
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
    @action(detail=False, methods=['post'], url_path='importar')
    def importar(self, request):
        pdf_file = request.FILES.get('file')
        if not pdf_file:
            return error_response("El archivo 'file' es requerido.", status=400)
            
        if not pdf_file.name.endswith('.pdf'):
            return error_response("El archivo debe ser un PDF válido.", status=400)
            
        # Write to a temporary file inside workspace directory to parse safely
        temp_dir = os.path.join(settings.BASE_DIR, 'temp')
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
                
            for row in rows:
                nombre = row["nombre"]
                apellido = row["apellido"]
                email = row["email"]
                departamento = row["departamento"]
                
                # Check duplicate by email locally
                if Docente.objects.filter(email=email).exists():
                    omitidos += 1
                    continue
                    
                # Create user in MS-1 Auth
                temp_pwd = str(uuid.uuid4())[:8]
                user_id, err_msg = create_user_in_auth(email, f"{nombre} {apellido}".strip(), "docente", temp_pwd)
                
                if not user_id:
                    errores.append({"email": email, "error": err_msg or "Error en gRPC de MS-1 Auth"})
                    continue
                    
                try:
                    Docente.objects.create(
                        usuario_id=user_id,
                        nombre=nombre,
                        apellido=apellido,
                        email=email,
                        departamento=departamento
                    )
                    creados += 1
                except Exception as e:
                    errores.append({"email": email, "error": f"Error de BD local: {str(e)}"})
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
        summary = {
            "creados": creados,
            "omitidos": omitidos,
            "errores": len(errores)
        }
        return success_response(summary, message="Importación de docentes completada")


class AlumnoViewSet(viewsets.ModelViewSet):
    """ViewSet para CRUD e Importación de Alumnos."""
    queryset = Alumno.objects.all().order_by("-fecha_creacion")
    serializer_class = AlumnoSerializer
    pagination_class = AGMPagination

    @jwt_required(roles=["admin"])
    @action(detail=False, methods=['post'], url_path='importar/preview')
    def importar_preview(self, request):
        """Parsear archivo y retornar preview de datos válidos/errores."""
        archivo = request.FILES.get('archivo')
        if not archivo:
            return error_response("No se proporcionó ningún archivo ('archivo' multipart esperado).", status=400)
            
        validas, errores = parse_alumnos_file(archivo, archivo.name)
        return success_response({
            "validas": validas,
            "errores": errores,
            "total_validas": len(validas),
            "total_errores": len(errores)
        })

    @jwt_required(roles=["admin"])
    @action(detail=False, methods=['post'], url_path='importar/confirmar')
    def importar_confirmar(self, request):
        """Ejecutar upsert de alumnos confirmados."""
        alumnos_data = request.data.get('alumnos', [])
        if not alumnos_data:
            return error_response("No se proporcionaron datos de alumnos (JSON con lista 'alumnos' esperado).", status=400)
            
        creados = 0
        actualizados = 0
        
        try:
            with transaction.atomic():
                for data in alumnos_data:
                    matricula = data.get('matricula')
                    if not matricula:
                        continue
                        
                    usuario_id = int(data.get('usuario_id') or 0)
                    clave_acceso = (data.get('clave_acceso') or '').strip()
                    materia_id = int(data.get('materia_id') or 0)
                    nombre_completo = f"{data.get('nombre', '')} {data.get('apellido', '')}".strip()

                    alumno, created = Alumno.objects.update_or_create(
                        matricula=matricula,
                        defaults={
                            "nombre": data.get('nombre'),
                            "apellido": data.get('apellido'),
                            "email": data.get('email'),
                            "carrera": data.get('carrera', 'ICC'),
                            "semestre": data.get('semestre', 1),
                            "usuario_id": usuario_id,
                        },
                    )

                    if created:
                        creados += 1
                        if not alumno.usuario_id:
                            uid, clave_ms1, err = create_user_alumno(
                                alumno.email,
                                nombre_completo or alumno.matricula,
                            )
                            if uid:
                                alumno.usuario_id = uid
                                alumno.save(update_fields=['usuario_id'])
                                clave_acceso = clave_acceso or (clave_ms1 or '')
                            elif err:
                                logger.warning(
                                    'Import %s: usuario MS-1 no creado (%s); import continúa',
                                    matricula,
                                    err,
                                )
                        send_bienvenida(
                            alumno,
                            materia_id=materia_id,
                            clave_acceso=clave_acceso,
                        )
                    else:
                        actualizados += 1
                        
            return success_response({
                "creados": creados,
                "actualizados": actualizados
            }, message="Importación completada con éxito.")
            
        except Exception as e:
            return error_response(f"Error durante la persistencia de datos: {str(e)}", status=500)

    @jwt_required()
    @action(detail=False, methods=['get'], url_path='por-materia')
    def por_materia(self, request):
        """Listar alumnos activos en una materia específica."""
        materia_id = request.query_params.get('materia_id')
        if not materia_id:
            return error_response("El parámetro 'materia_id' es requerido.", status=400)
            
        try:
            materia_id = int(materia_id)
        except ValueError:
            return error_response("El parámetro 'materia_id' debe ser un número entero.", status=400)
            
        # Filtrar inscripciones activas para la materia
        queryset = InscripcionMateria.objects.filter(
            materia_id=materia_id,
            activa=True
        ).select_related('alumno').order_by('alumno__apellido', 'alumno__nombre')
        
        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = InscripcionMateriaSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = InscripcionMateriaSerializer(queryset, many=True)
        return success_response(serializer.data)

    @jwt_required(roles=["admin"])
    @action(detail=True, methods=['post'], url_path='baja-materia')
    def baja_materia(self, request, pk=None):
        """Da de baja una materia de forma irreversible para un alumno."""
        alumno = self.get_object()
        materia_id = request.data.get('materia_id')
        
        if not materia_id:
            return error_response("El campo 'materia_id' es requerido en el cuerpo JSON.", status=400)
            
        try:
            with transaction.atomic():
                # select_for_update para evitar condiciones de carrera
                inscripcion = InscripcionMateria.objects.select_for_update().filter(
                    alumno=alumno,
                    materia_id=materia_id
                ).first()
                
                if not inscripcion:
                    return error_response("No se encontró una inscripción para esta materia.", status=404)
                    
                if not inscripcion.activa:
                    return error_response("baja ya procesada", status=400)
                    
                # Ejecutar baja irreversible
                inscripcion.activa = False
                inscripcion.fecha_baja = timezone.now()
                inscripcion.save()
                
                docente_id = get_materia_docente_id(int(materia_id)) or 0
                send_baja_notif(inscripcion, docente_id=docente_id)
                
            return success_response({
                "alumno": alumno.matricula,
                "materia_id": materia_id,
                "fecha_baja": inscripcion.fecha_baja
            }, message="Baja de materia procesada exitosamente.")
            
        except Exception as e:
            return error_response(f"Error inesperado al procesar la baja: {str(e)}", status=500)
