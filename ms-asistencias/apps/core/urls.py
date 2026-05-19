"""URL configuration for apps.core."""

from rest_framework.routers import DefaultRouter
from django.urls import path
from apps.core.views import (
    SesionAsistenciaViewSet,
    RegistroAsistenciaViewSet,
    qr_generate,
    asistencia_registrar,
)

router = DefaultRouter()
router.register(r'sesiones', SesionAsistenciaViewSet, basename='sesion')
router.register(r'registros', RegistroAsistenciaViewSet, basename='registro')

urlpatterns = router.urls + [
    path('qr/generate/', qr_generate, name='qr-generate'),
    path('asistencias/registrar/', asistencia_registrar, name='asistencia-registrar'),
]
