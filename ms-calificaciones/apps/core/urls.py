from django.urls import path

from apps.core.views import cerrar_materia

urlpatterns = [
    path('materias/<int:materia_id>/cerrar', cerrar_materia, name='cerrar-materia'),
]
