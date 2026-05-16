from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from apps.core.models import Docente, Alumno, InscripcionMateria
from apps.core.serializers import DocenteSerializer, AlumnoSerializer, InscripcionMateriaSerializer
from utils.pagination import AGMPagination
from utils.responses import success_response, error_response
from utils.excel_parser import parse_alumnos_file
from utils.notificaciones_client import send_bienvenida, send_baja_notif


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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(serializer.data, message="Docente actualizado")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(None, message="Docente eliminado", status=status.HTTP_200_OK)


class AlumnoViewSet(viewsets.ModelViewSet):
    """ViewSet para CRUD e Importación de Alumnos."""
    queryset = Alumno.objects.all().order_by("-fecha_creacion")
    serializer_class = AlumnoSerializer
    pagination_class = AGMPagination

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
                        
                    alumno, created = Alumno.objects.update_or_create(
                        matricula=matricula,
                        defaults={
                            "nombre": data.get('nombre'),
                            "apellido": data.get('apellido'),
                            "email": data.get('email'),
                            "carrera": data.get('carrera', 'ICC'),
                            "semestre": data.get('semestre', 1),
                            "usuario_id": data.get('usuario_id', 0) # Placeholder hasta ISSUE-502
                        }
                    )
                    
                    if created:
                        creados += 1
                        # Intentar notificar bienvenida (graceful error handling dentro del cliente)
                        send_bienvenida(alumno)
                    else:
                        actualizados += 1
                        
            return success_response({
                "creados": creados,
                "actualizados": actualizados
            }, message="Importación completada con éxito.")
            
        except Exception as e:
            return error_response(f"Error durante la persistencia de datos: {str(e)}", status=500)

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
                
                # Notificar a MS-6 (mockeado en tests)
                send_baja_notif(inscripcion)
                
            return success_response({
                "alumno": alumno.matricula,
                "materia_id": materia_id,
                "fecha_baja": inscripcion.fecha_baja
            }, message="Baja de materia procesada exitosamente.")
            
        except Exception as e:
            return error_response(f"Error inesperado al procesar la baja: {str(e)}", status=500)
