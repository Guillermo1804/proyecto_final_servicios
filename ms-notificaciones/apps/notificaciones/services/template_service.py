from django.template.loader import render_to_string


class TemplateService:
    """Renderizado HTML de correos transaccionales AGM."""

    @staticmethod
    def render_bienvenida(context: dict) -> str:
        return render_to_string('emails/bienvenida.html', context)

    @staticmethod
    def render_baja(context: dict) -> str:
        return render_to_string('emails/baja.html', context)

    @staticmethod
    def render_cierre_materia(context: dict) -> str:
        return render_to_string('emails/cierre_materia.html', context)

    @staticmethod
    def render_reset_password(context: dict) -> str:
        return render_to_string('emails/reset_password.html', context)
