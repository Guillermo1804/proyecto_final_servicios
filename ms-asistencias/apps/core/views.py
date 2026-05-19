"""REST API views for MS-5 Asistencias QR."""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.core.models import SesionAsistencia, RegistroAsistencia
from apps.core.serializers import (
    SesionAsistenciaSerializer,
    IniciarSesionSerializer,
    RegistroAsistenciaSerializer,
    RegistroAsistenciaListSerializer,
    EstadisticasAsistenciaSerializer,
    GenerarQRSerializer,
    QRTokenResponseSerializer,
    RegistrarAsistenciaSerializer,
    RegistroAsistenciaResponseSerializer,
)
from apps.core.services import SesionAsistenciaService
from apps.core.qr_service import QRTokenService
from apps.core.attendance_service import AsistenciaRegistroService
from apps.core.estadisticas_service import EstadisticasService
from apps.core.utils import get_stats


class SesionAsistenciaViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance sessions."""
    
    queryset = SesionAsistencia.objects.all()
    serializer_class = SesionAsistenciaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by docente_id or materia_id if provided."""
        queryset = SesionAsistencia.objects.all()
        
        materia_id = self.request.query_params.get('materia_id')
        docente_id = self.request.query_params.get('docente_id')
        activa = self.request.query_params.get('activa')
        
        if materia_id:
            queryset = queryset.filter(materia_id=materia_id)
        
        if docente_id:
            queryset = queryset.filter(docente_id=docente_id)
        
        if activa in ['true', 'True', '1', 'yes']:
            queryset = queryset.filter(activa=True)
        elif activa in ['false', 'False', '0', 'no']:
            queryset = queryset.filter(activa=False)
        
        return queryset.order_by('-fecha_inicio')
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def iniciar(self, request):
        """
        POST /sesiones/iniciar
        
        Create a new attendance session for a subject.
        
        Body:
        {
            "materia_id": 1,
            "docente_id": 5
        }
        
        Returns:
        - 201: Sesión creada
        - 400: Validación o sesión duplicada
        """
        serializer = IniciarSesionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        materia_id = serializer.validated_data['materia_id']
        docente_id = serializer.validated_data['docente_id']
        
        try:
            sesion, message = SesionAsistenciaService.crear_sesion(
                materia_id=materia_id,
                docente_id=docente_id
            )
            
            response_serializer = SesionAsistenciaSerializer(sesion)
            return Response(
                {
                    'message': message,
                    'sesion': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def cerrar(self, request, pk=None):
        """
        DELETE /sesiones/{id}/cerrar
        
        Close an active session.
        
        Returns:
        - 200: Sesión cerrada
        - 404: Sesión no encontrada
        - 400: Sesión ya cerrada
        """
        sesion = get_object_or_404(SesionAsistencia, id=pk)
        
        success, message = SesionAsistenciaService.cerrar_sesion(sesion.id)
        
        if success:
            sesion.refresh_from_db()
            serializer = SesionAsistenciaSerializer(sesion)
            return Response(
                {
                    'message': message,
                    'sesion': serializer.data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def confirmar(self, request, pk=None):
        """
        POST /sesiones/{id}/confirmar

        Confirm session and freeze attendance records.

        Returns:
        - 200: Sesión confirmada
        - 404: Sesión no encontrada
        - 400: Sesión no activa o ya confirmada
        """
        sesion = get_object_or_404(SesionAsistencia, id=pk)

        success, message = SesionAsistenciaService.confirmar_sesion(sesion.id)

        if success:
            sesion.refresh_from_db()
            serializer = SesionAsistenciaSerializer(sesion)
            return Response(
                {
                    'message': message,
                    'sesion': serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='solicitar-nueva',
    )
    def solicitar_nueva(self, request, pk=None):
        """
        POST /sesiones/{id}/solicitar-nueva

        Invalidate current session and unlock new list creation.

        Returns:
        - 200: Sesión invalidada y habilitada nueva lista
        - 404: Sesión no encontrada
        - 400: Error de validación
        """
        sesion = get_object_or_404(SesionAsistencia, id=pk)

        success, message = SesionAsistenciaService.solicitar_nueva_lista(sesion.id)

        if success:
            sesion.refresh_from_db()
            serializer = SesionAsistenciaSerializer(sesion)
            return Response(
                {
                    'message': message,
                    'sesion': serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def activa(self, request):
        """
        GET /sesiones/activa?materia_id=1
        
        Get the currently active session for a subject.
        
        Returns:
        - 200: Sesión activa (o null si no existe)
        - 400: materia_id requerido
        """
        materia_id = request.query_params.get('materia_id')
        
        if not materia_id:
            return Response(
                {'error': 'materia_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            materia_id = int(materia_id)
        except ValueError:
            return Response(
                {'error': 'materia_id debe ser un número'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sesion = SesionAsistenciaService.obtener_sesion_activa(materia_id)
        
        if sesion:
            serializer = SesionAsistenciaSerializer(sesion)
            return Response(
                {
                    'activa': True,
                    'sesion': serializer.data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'activa': False,
                    'sesion': None,
                    'message': f'No hay sesión activa para materia {materia_id}'
                },
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request, pk=None):
        """
        GET /sesiones/{id}/stats
        
        Get real-time statistics for a session.
        
        Returns:
        - 200: Estadísticas en tiempo real
        - 404: Sesión no encontrada
        
        Response:
        {
            "sesion_id": 1,
            "materia_id": 3,
            "docente_id": 5,
            "presentes": 10,
            "retardos": 2,
            "ausentes": 0,
            "total_registrados": 12,
            "estado_sesion": "activa",
            "vigente": true,
            "minutos_transcurridos": 5,
            "fecha_inicio": "2026-05-18T10:00:00Z",
            "fecha_fin_teorica": "2026-05-18T10:10:00Z"
        }
        """
        try:
            stats_data = EstadisticasService.obtener_stats_sesion(pk)
            return Response(stats_data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo estadísticas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stats_materia(self, request):
        """
        GET /sesiones/stats_materia?materia_id=3
        
        Get aggregate statistics for a subject (all sessions and registrations).
        
        Query params:
        - materia_id: Subject ID (required)
        
        Returns:
        - 200: Estadísticas agregadas
        - 400: materia_id requerido
        """
        materia_id = request.query_params.get('materia_id')
        
        if not materia_id:
            return Response(
                {'error': 'materia_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            materia_id = int(materia_id)
        except ValueError:
            return Response(
                {'error': 'materia_id debe ser un número'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stats_data = EstadisticasService.obtener_stats_materia_resumen(materia_id)
            return Response(stats_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo estadísticas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RegistroAsistenciaViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance records."""
    
    queryset = RegistroAsistencia.objects.all()
    serializer_class = RegistroAsistenciaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by sesion_id or alumno_id if provided."""
        queryset = RegistroAsistencia.objects.all()
        
        sesion_id = self.request.query_params.get('sesion_id')
        alumno_id = self.request.query_params.get('alumno_id')
        materia_id = self.request.query_params.get('materia_id')
        estado = self.request.query_params.get('estado')
        
        if sesion_id:
            queryset = queryset.filter(sesion__id=sesion_id)
        
        if alumno_id:
            queryset = queryset.filter(alumno_id=alumno_id)
        
        if materia_id:
            queryset = queryset.filter(sesion__materia_id=materia_id)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset.order_by('-fecha_registro')
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def por_materia_hoy(self, request):
        """
        GET /registros/por_materia_hoy?materia_id=1
        
        Get today's attendance records for a subject.
        """
        materia_id = request.query_params.get('materia_id')
        
        if not materia_id:
            return Response(
                {'error': 'materia_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            materia_id = int(materia_id)
        except ValueError:
            return Response(
                {'error': 'materia_id debe ser un número'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.utils import timezone
        today = timezone.now().date()
        
        registros = RegistroAsistencia.objects.filter(
            sesion__materia_id=materia_id,
            fecha_registro__date=today
        ).order_by('-fecha_registro')
        
        serializer = RegistroAsistenciaListSerializer(registros, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def historial(self, request):
        """
        GET /registros/historial?materia_id=1&page=1&limit=10&fecha_desde=2026-05-01&fecha_hasta=2026-05-18
        
        Get historical attendance records for a subject with pagination.
        
        Query params:
        - materia_id: Subject ID (required)
        - page: Page number (default 1)
        - limit: Records per page (default 20, max 100)
        - fecha_desde: Start date (YYYY-MM-DD, optional)
        - fecha_hasta: End date (YYYY-MM-DD, optional)
        """
        materia_id = request.query_params.get('materia_id')
        
        if not materia_id:
            return Response(
                {'error': 'materia_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            materia_id = int(materia_id)
        except ValueError:
            return Response(
                {'error': 'materia_id debe ser un número'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Pagination parameters
        try:
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 20))
            
            if limit > 100:
                limit = 100
            if limit < 1:
                limit = 1
            if page < 1:
                page = 1
        except ValueError:
            return Response(
                {'error': 'page y limit deben ser números'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Date filtering
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        
        queryset = RegistroAsistencia.objects.filter(
            sesion__materia_id=materia_id
        ).order_by('-fecha_registro')
        
        if fecha_desde:
            try:
                from datetime import datetime
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_registro__date__gte=fecha_desde_obj)
            except ValueError:
                return Response(
                    {'error': 'Formato fecha_desde inválido (usar YYYY-MM-DD)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if fecha_hasta:
            try:
                from datetime import datetime
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_registro__date__lte=fecha_hasta_obj)
            except ValueError:
                return Response(
                    {'error': 'Formato fecha_hasta inválido (usar YYYY-MM-DD)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get total count
        total = queryset.count()
        
        # Calculate pagination
        offset = (page - 1) * limit
        registros = queryset[offset:offset + limit]
        
        serializer = RegistroAsistenciaListSerializer(registros, many=True)
        
        return Response(
            {
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': (total + limit - 1) // limit,
                'results': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def alumno_materia(self, request):
        """
        GET /registros/alumno_materia?alumno_id=5&materia_id=3
        
        Get attendance records for a specific student in a specific subject.
        
        Query params:
        - alumno_id: Student ID (required)
        - materia_id: Subject ID (required)
        
        Note: Alumno can only query their own records; admin/docente can query any.
        """
        alumno_id = request.query_params.get('alumno_id')
        materia_id = request.query_params.get('materia_id')
        
        if not alumno_id or not materia_id:
            return Response(
                {'error': 'alumno_id y materia_id son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            alumno_id = int(alumno_id)
            materia_id = int(materia_id)
        except ValueError:
            return Response(
                {'error': 'alumno_id y materia_id deben ser números'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter by student and subject
        registros = RegistroAsistencia.objects.filter(
            alumno_id=alumno_id,
            sesion__materia_id=materia_id
        ).order_by('-fecha_registro')
        
        # Summary statistics
        total = registros.count()
        presentes = registros.filter(estado='presente').count()
        retardos = registros.filter(estado='retardo').count()
        ausentes = registros.filter(estado='ausente').count()
        
        serializer = RegistroAsistenciaListSerializer(registros, many=True)
        
        return Response(
            {
                'alumno_id': alumno_id,
                'materia_id': materia_id,
                'total_registros': total,
                'presentes': presentes,
                'retardos': retardos,
                'ausentes': ausentes,
                'porcentaje_asistencia': (presentes / total * 100) if total > 0 else 0,
                'registros': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stats_alumno_materia(self, request):
        """
        GET /registros/stats_alumno_materia?alumno_id=5&materia_id=3
        
        Get attendance statistics for a student in a specific subject.
        
        Query params:
        - alumno_id: Student ID (required)
        - materia_id: Subject ID (required)
        
        Returns summary statistics without individual records.
        """
        alumno_id = request.query_params.get('alumno_id')
        materia_id = request.query_params.get('materia_id')
        
        if not alumno_id or not materia_id:
            return Response(
                {'error': 'alumno_id y materia_id son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            alumno_id = int(alumno_id)
            materia_id = int(materia_id)
        except ValueError:
            return Response(
                {'error': 'alumno_id y materia_id deben ser números'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stats_data = EstadisticasService.obtener_stats_alumno_materia(alumno_id, materia_id)
            return Response(stats_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo estadísticas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def qr_generate(request):
    """
    GET /api/qr/generate?materia_id=1&alumno_id=1
    
    Generate a QR token for attendance registration.
    
    Query params:
    - materia_id: Subject ID (required)
    - alumno_id: Student ID (required)
    
    Returns:
    - 200: QR token generated
    - 400: Validation error
    - 404: No active session or student not enrolled
    """
    # Parse query parameters
    materia_id = request.query_params.get('materia_id')
    alumno_id = request.query_params.get('alumno_id')
    
    if not materia_id or not alumno_id:
        return Response(
            {'error': 'materia_id y alumno_id son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        materia_id = int(materia_id)
        alumno_id = int(alumno_id)
    except ValueError:
        return Response(
            {'error': 'materia_id y alumno_id deben ser números'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        qr_data = QRTokenService.generar_token_qr(
            alumno_id=alumno_id,
            materia_id=materia_id
        )
        
        serializer = QRTokenResponseSerializer(qr_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Error generando QR: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def asistencia_registrar(request):
    """
    POST /api/asistencias/registrar/
    
    Register attendance from QR token.
    
    Body:
    {
        "encoded_payload": "base64-encoded-qr-payload"
    }
    
    Returns:
    - 201: Asistencia registrada exitosamente
    - 400: Validación fallida, QR inválido, anti-replay, etc
    - 500: Error interno
    """
    serializer = RegistrarAsistenciaSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    encoded_payload = serializer.validated_data['encoded_payload']
    
    try:
        resultado = AsistenciaRegistroService.registrar_asistencia(
            encoded_payload=encoded_payload
        )
        
        response_serializer = RegistroAsistenciaResponseSerializer(resultado)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Error registrando asistencia: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
