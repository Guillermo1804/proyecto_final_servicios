from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "MS-2 Periodos & Materias"

    def ready(self) -> None:
        import apps.core.event_bus.signals  # noqa: F401
