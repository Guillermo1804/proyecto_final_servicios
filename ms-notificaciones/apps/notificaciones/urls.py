from django.urls import path

from apps.notificaciones.views import (
    BajaView,
    BienvenidaView,
    CierreMateriaView,
    ResetPasswordView,
)

app_name = 'notificaciones'

urlpatterns = [
    path('bienvenida', BienvenidaView.as_view(), name='bienvenida'),
    path('baja', BajaView.as_view(), name='baja'),
    path('cierre-materia', CierreMateriaView.as_view(), name='cierre-materia'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
]
