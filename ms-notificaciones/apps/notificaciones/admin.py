from django.contrib import admin

from apps.notificaciones.models import HistorialCorreo


@admin.register(HistorialCorreo)
class HistorialCorreoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tipo',
        'destinatario_email',
        'asunto',
        'exitoso',
        'enviado_en',
    )
    list_filter = ('tipo', 'exitoso')
    search_fields = ('destinatario_email', 'asunto')
    readonly_fields = ('enviado_en',)
