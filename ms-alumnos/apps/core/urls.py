from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import DocenteViewSet, AlumnoViewSet

router = DefaultRouter()
router.register(r"docentes", DocenteViewSet, basename="docentes")
router.register(r"alumnos", AlumnoViewSet, basename="alumnos")

urlpatterns = [
    path("", include(router.urls)),
]
