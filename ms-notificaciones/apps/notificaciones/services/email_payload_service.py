"""Envio de correos usando solo datos del payload del evento (sin gRPC MS-2/MS-3)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from decouple import config
from django.conf import settings
from django.core.mail import send_mail

from apps.notificaciones.models import EstadoEnvioCorreo, TipoCorreo
from apps.notificaciones.services.historial_service import HistorialService
from apps.notificaciones.services.template_service import TemplateService

logger = logging.getLogger(__name__)


class EmailPayloadService:
    def __init__(self) -> None:
        self.templates = TemplateService()
        self.historial = HistorialService()
        self.frontend_url = config('FRONTEND_URL', default='http://localhost:4200').rstrip('/')
        self.simulate_smtp_failure = config('SMTP_SIMULATE_FAILURE', default=False, cast=bool)

    def send_bienvenida_from_payload(
        self, payload: dict[str, Any], *, event_id: uuid.UUID
    ) -> dict[str, Any]:
        email = payload.get('email', '')
        clave = (payload.get('clave_acceso') or '').strip()
        if not clave:
            return self._skip(
                TipoCorreo.BIENVENIDA,
                email,
                'Bienvenida AGM',
                event_id,
                'clave_acceso vacía — omitido',
            )
        materia_nombre = payload.get('materia_nombre') or 'AGM — Facultad de Ciencias de la Computación'
        asunto = f'Bienvenida a AGM — {materia_nombre}'
        context = {
            'alumno_nombre': payload.get('nombre', ''),
            'matricula': payload.get('matricula', ''),
            'materia_nombre': materia_nombre,
            'nrc': payload.get('nrc') or '—',
            'seccion': payload.get('seccion') or '—',
            'clave_acceso': clave,
            'login_url': self.frontend_url,
        }
        html = self.templates.render_bienvenida(context)
        return self._send(
            tipo=TipoCorreo.BIENVENIDA,
            to_email=email,
            asunto=asunto,
            html_body=html,
            event_id=event_id,
        )

    def send_baja_from_payload(
        self, payload: dict[str, Any], *, event_id: uuid.UUID
    ) -> dict[str, Any]:
        docente_email = (payload.get('docente_email') or '').strip()
        if not docente_email:
            return self._skip(
                TipoCorreo.BAJA,
                '',
                'Baja de alumno',
                event_id,
                'docente_email vacío',
            )
        materia_nombre = payload.get('materia_nombre') or 'Materia'
        asunto = f'Baja de alumno — {materia_nombre} ({payload.get("nrc", "")})'
        context = {
            'docente_nombre': payload.get('docente_nombre') or 'Docente',
            'alumno_nombre': payload.get('nombre', ''),
            'matricula': payload.get('matricula', ''),
            'materia_nombre': materia_nombre,
            'nrc': payload.get('nrc') or '—',
            'seccion': payload.get('seccion') or '—',
        }
        html = self.templates.render_baja(context)
        return self._send(
            tipo=TipoCorreo.BAJA,
            to_email=docente_email,
            asunto=asunto,
            html_body=html,
            event_id=event_id,
        )

    def send_reset_from_payload(
        self, payload: dict[str, Any], *, event_id: uuid.UUID
    ) -> dict[str, Any]:
        email = payload.get('email', '')
        reset_url = payload.get('reset_url', '')
        if not email or not reset_url:
            return self._skip(
                TipoCorreo.RESET_PASSWORD,
                email or '',
                'Restablece tu contraseña AGM',
                event_id,
                'email o reset_url faltante',
            )
        asunto = 'Restablece tu contraseña — AGM'
        context = {
            'reset_url': reset_url,
            'frontend_url': self.frontend_url,
        }
        html = self.templates.render_reset_password(context)
        return self._send(
            tipo=TipoCorreo.RESET_PASSWORD,
            to_email=email,
            asunto=asunto,
            html_body=html,
            event_id=event_id,
        )

    def send_cierre_from_payload(
        self, payload: dict[str, Any], *, event_id: uuid.UUID
    ) -> dict[str, Any]:
        alumnos = payload.get('alumnos') or []
        materia_nombre = payload.get('nombre') or f'Materia {payload.get("materia_id")}'
        nrc = payload.get('nrc') or '—'
        if not alumnos:
            logger.info(
                'materia_closed_sin_alumnos_en_payload',
                extra={'event_id': str(event_id), 'materia_id': payload.get('materia_id')},
            )
            return {
                'success': True,
                'message': 'Sin lista de alumnos en payload — sin envíos masivos',
                'enviados': 0,
            }
        asunto = f'Materia cerrada — {materia_nombre} ({nrc})'
        enviados = 0
        for alumno in alumnos:
            email = alumno.get('email')
            if not email:
                continue
            context = {
                'alumno_nombre': alumno.get('nombre', ''),
                'matricula': alumno.get('matricula', ''),
                'materia_nombre': materia_nombre,
                'nrc': nrc,
                'seccion': payload.get('seccion') or '—',
                'periodo_nombre': payload.get('periodo_nombre') or '—',
                'login_url': self.frontend_url,
            }
            html = self.templates.render_cierre_materia(context)
            result = self._send(
                tipo=TipoCorreo.CIERRE_MATERIA,
                to_email=email,
                asunto=asunto,
                html_body=html,
                event_id=event_id,
            )
            if result.get('success'):
                enviados += 1
        return {'success': True, 'enviados': enviados}

    def _send(
        self,
        *,
        tipo: str,
        to_email: str,
        asunto: str,
        html_body: str,
        event_id: uuid.UUID,
    ) -> dict[str, Any]:
        registro = self.historial.registrar(
            tipo=tipo,
            destinatario_email=to_email,
            asunto=asunto,
            cuerpo=html_body,
            exitoso=False,
            event_id=event_id,
            estado_envio=EstadoEnvioCorreo.RETRYING,
        )
        if self.simulate_smtp_failure:
            self.historial.actualizar_estado(
                registro,
                exitoso=False,
                error_msg='SMTP_SIMULATE_FAILURE=true',
                estado_envio=EstadoEnvioCorreo.FAILED,
            )
            return {
                'success': False,
                'message': 'SMTP simulado fallido',
                'historial_id': registro.id,
            }
        plain = 'Consulta este correo en un cliente compatible con HTML.'
        try:
            sent = send_mail(
                subject=asunto,
                message=plain,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_body,
                fail_silently=False,
            )
            if sent != 1:
                raise RuntimeError(f'send_mail devolvió {sent}')
            self.historial.actualizar_estado(
                registro,
                exitoso=True,
                estado_envio=EstadoEnvioCorreo.SENT,
            )
            return {
                'success': True,
                'historial_id': registro.id,
                'destinatario_email': to_email,
            }
        except Exception as exc:
            logger.exception('smtp_failed event_id=%s', event_id)
            self.historial.actualizar_estado(
                registro,
                exitoso=False,
                error_msg=str(exc)[:2000],
                estado_envio=EstadoEnvioCorreo.FAILED,
            )
            raise

    def _skip(
        self,
        tipo: str,
        to_email: str,
        asunto: str,
        event_id: uuid.UUID,
        reason: str,
    ) -> dict[str, Any]:
        self.historial.registrar(
            tipo=tipo,
            destinatario_email=to_email or 'omitido@agm.local',
            asunto=asunto,
            cuerpo='',
            exitoso=True,
            error_msg=reason,
            event_id=event_id,
            estado_envio=EstadoEnvioCorreo.SENT,
        )
        return {'success': True, 'skipped': True, 'message': reason}
