from django.contrib import admin

from apps.reportes.models import ReporteGenerado


@admin.register(ReporteGenerado)
class ReporteGeneradoAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo', 'usuario_id', 'formato', 'generado_en')
    list_filter = ('tipo', 'formato')
    search_fields = ('usuario_id',)
    readonly_fields = ('generado_en',)
