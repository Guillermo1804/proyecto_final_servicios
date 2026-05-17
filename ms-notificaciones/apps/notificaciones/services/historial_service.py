from typing import Optional

from apps.notificaciones.models import HistorialCorreo, TipoCorreo


class HistorialService:
    @staticmethod
    def registrar(
        *,
        tipo: str,
        destinatario_email: str,
        asunto: str,
        cuerpo: str,
        exitoso: bool,
        error_msg: Optional[str] = None,
    ) -> HistorialCorreo:
        if tipo not in TipoCorreo.values:
            raise ValueError(f'Tipo de correo inválido: {tipo}')
        return HistorialCorreo.objects.create(
            tipo=tipo,
            destinatario_email=destinatario_email,
            asunto=asunto[:255],
            cuerpo=cuerpo,
            exitoso=exitoso,
            error_msg=error_msg or None,
        )
