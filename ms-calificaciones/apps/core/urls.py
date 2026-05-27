from django.urls import path

from apps.core.views import (
    actividades,
    cerrar_materia,
    crear_calificacion,
    concentrado,
    editar_eliminar_actividad,
    editar_eliminar_calificacion,
    importar_calificaciones,
    importar_ponderaciones,
    ponderaciones,
    imprimir_lista,
)

urlpatterns = [
    path('ponderaciones/<int:materia_id>', ponderaciones, name='ponderaciones'),
    path('ponderaciones/<int:materia_id>/importar', importar_ponderaciones, name='ponderaciones-importar'),
    path('actividades', actividades, name='actividades'),
    path('actividades/<int:actividad_id>', editar_eliminar_actividad, name='editar-eliminar-actividad'),
    path('calificaciones', crear_calificacion, name='crear-calificacion'),
    path('calificaciones/importar/<int:materia_id>', importar_calificaciones, name='importar-calificaciones'),
    path('concentrado/<int:materia_id>', concentrado, name='concentrado'),
    path('calificaciones/<int:calificacion_id>', editar_eliminar_calificacion, name='editar-eliminar-calificacion'),
    path('materias/<int:materia_id>/cerrar', cerrar_materia, name='cerrar-materia'),
    path('materias/<int:materia_id>/imprimir-lista', imprimir_lista, name='imprimir-lista'),
]
