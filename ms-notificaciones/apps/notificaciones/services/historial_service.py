from __future__ import annotations

import uuid
from typing import Optional

from apps.notificaciones.models import EstadoEnvioCorreo, HistorialCorreo, TipoCorreo


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
        event_id: uuid.UUID | str | None = None,
        estado_envio: str | None = None,
    ) -> HistorialCorreo:
        if tipo not in TipoCorreo.values:
            raise ValueError(f'Tipo de correo inválido: {tipo}')
        if estado_envio is None:
            estado_envio = (
                EstadoEnvioCorreo.SENT if exitoso else EstadoEnvioCorreo.FAILED
            )
        eid = uuid.UUID(str(event_id)) if event_id else None
        return HistorialCorreo.objects.create(
            tipo=tipo,
            destinatario_email=destinatario_email,
            asunto=asunto[:255],
            cuerpo=cuerpo,
            exitoso=exitoso,
            error_msg=error_msg or None,
            event_id=eid,
            estado_envio=estado_envio,
        )

    @staticmethod
    def actualizar_estado(
        registro: HistorialCorreo,
        *,
        exitoso: bool,
        error_msg: str | None = None,
        estado_envio: str,
    ) -> HistorialCorreo:
        registro.exitoso = exitoso
        registro.error_msg = error_msg
        registro.estado_envio = estado_envio
        registro.save(update_fields=['exitoso', 'error_msg', 'estado_envio'])
        return registro
