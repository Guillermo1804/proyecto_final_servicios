from django.urls import path

from apps.reportes.views import estadisticas_views, reportes_views

urlpatterns = [
    path(
        'calificaciones/<int:materia_id>',
        reportes_views.reporte_calificaciones,
        name='reporte-calificaciones',
    ),
    path(
        'asistencias/<int:materia_id>',
        reportes_views.reporte_asistencias,
        name='reporte-asistencias',
    ),
    path(
        'docente/<int:usuario_id>',
        estadisticas_views.estadisticas_docente,
        name='estadisticas-docente',
    ),
    path(
        'alumno/<int:alumno_id>',
        estadisticas_views.estadisticas_alumno,
        name='estadisticas-alumno',
    ),
]
