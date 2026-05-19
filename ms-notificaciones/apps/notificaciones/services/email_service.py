import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from decouple import config
from django.conf import settings
from django.core.mail import send_mail

from apps.notificaciones.exceptions import (
    AlumnoNotFound,
    DocenteNotFound,
    MateriaNotFound,
    NotificacionesDomainError,
    UpstreamGrpcError,
    UpstreamUnavailable,
)
from apps.notificaciones.models import TipoCorreo
from apps.notificaciones.services.data_provider import (
    GrpcDataProvider,
    NotificacionesDataProvider,
    PlaceholderDataProvider,
)
from apps.notificaciones.services.historial_service import HistorialService
from apps.notificaciones.services.template_service import TemplateService
from config.agm_env import env_bool

logger = logging.getLogger(__name__)


def _default_data_provider() -> NotificacionesDataProvider:
    if env_bool('USE_PLACEHOLDER_DATA', default=False):
        return PlaceholderDataProvider()
    return GrpcDataProvider()


class EmailService:
    """Orquesta datos, plantillas, SMTP y auditoría (DRY para REST y gRPC)."""

    def __init__(self, data_provider: Optional[NotificacionesDataProvider] = None):
        self.data = data_provider if data_provider is not None else _default_data_provider()
        self.templates = TemplateService()
        self.historial = HistorialService()
        self.frontend_url = config('FRONTEND_URL', default='http://localhost:4200').rstrip('/')
        self.max_workers = config('EMAIL_MAX_WORKERS', default=5, cast=int)

    def send_bienvenida(
        self, alumno_id: int, materia_id: int, clave_acceso: str
    ) -> Dict[str, Any]:
        try:
            alumno = self.data.get_alumno(alumno_id)
        except NotificacionesDomainError as exc:
            return self._fail_from_domain(exc, TipoCorreo.BIENVENIDA, 'Bienvenida AGM')
        if not alumno:
            return self._fail(
                TipoCorreo.BIENVENIDA,
                '',
                'Bienvenida AGM',
                '',
                f'Alumno {alumno_id} no encontrado',
            )
        try:
            materia = self.data.get_materia(materia_id) if materia_id else None
        except NotificacionesDomainError as exc:
            return self._fail_from_domain(
                exc, TipoCorreo.BIENVENIDA, 'Bienvenida AGM', alumno.email
            )
        materia_nombre = materia.nombre if materia else 'AGM — Facultad de Ciencias de la Computación'
        asunto = f'Bienvenida a AGM — {materia_nombre}'
        context = {
            'alumno_nombre': alumno.nombre,
            'matricula': alumno.matricula,
            'materia_nombre': materia_nombre,
            'nrc': materia.nrc if materia else '—',
            'seccion': materia.seccion if materia else '—',
            'clave_acceso': clave_acceso,
            'login_url': self.frontend_url,
        }
        try:
            html = self.templates.render_bienvenida(context)
        except Exception as exc:
            return self._fail(
                TipoCorreo.BIENVENIDA,
                alumno.email,
                asunto,
                '',
                f'Error al renderizar plantilla: {exc}',
            )
        return self._send(
            tipo=TipoCorreo.BIENVENIDA,
            to_email=alumno.email,
            asunto=asunto,
            html_body=html,
        )

    def send_baja(
        self, alumno_id: int, docente_id: int, materia_id: int
    ) -> Dict[str, Any]:
        try:
            alumno = self.data.get_alumno(alumno_id)
            docente = self.data.get_docente_by_usuario_id(docente_id)
            materia = self.data.get_materia(materia_id)
        except NotificacionesDomainError as exc:
            return self._fail_from_domain(exc, TipoCorreo.BAJA, 'Baja de alumno')
        if not alumno:
            return self._fail(
                TipoCorreo.BAJA, '', 'Baja de alumno', '', f'Alumno {alumno_id} no encontrado'
            )
        if not docente:
            return self._fail(
                TipoCorreo.BAJA,
                '',
                'Baja de alumno',
                '',
                f'Docente usuario_id={docente_id} no encontrado',
            )
        if not materia:
            return self._fail(
                TipoCorreo.BAJA,
                docente.email,
                'Baja de alumno',
                '',
                f'Materia {materia_id} no encontrada',
            )
        asunto = f'Baja de alumno — {materia.nombre} ({materia.nrc})'
        context = {
            'docente_nombre': docente.nombre,
            'alumno_nombre': alumno.nombre,
            'matricula': alumno.matricula,
            'materia_nombre': materia.nombre,
            'nrc': materia.nrc,
            'seccion': materia.seccion,
        }
        try:
            html = self.templates.render_baja(context)
        except Exception as exc:
            return self._fail(
                TipoCorreo.BAJA,
                docente.email,
                asunto,
                '',
                f'Error al renderizar plantilla: {exc}',
            )
        return self._send(
            tipo=TipoCorreo.BAJA,
            to_email=docente.email,
            asunto=asunto,
            html_body=html,
        )

    def send_cierre_materia(self, materia_id: int) -> Dict[str, Any]:
        try:
            materia = self.data.get_materia(materia_id)
        except MateriaNotFound:
            return {
                'success': False,
                'message': f'Materia {materia_id} no encontrada',
                'enviados': 0,
                'fallidos': 0,
                'detalle': [],
            }
        except NotificacionesDomainError as exc:
            return {
                'success': False,
                'message': str(exc),
                'enviados': 0,
                'fallidos': 0,
                'detalle': [],
            }
        if not materia:
            return {
                'success': False,
                'message': f'Materia {materia_id} no encontrada',
                'enviados': 0,
                'fallidos': 0,
                'detalle': [],
            }
        try:
            alumnos = self.data.get_alumnos_by_materia(materia_id)
        except NotificacionesDomainError as exc:
            return {
                'success': False,
                'message': str(exc),
                'enviados': 0,
                'fallidos': 0,
                'detalle': [],
            }
        if not alumnos:
            return {
                'success': True,
                'message': 'No hay alumnos inscritos activos para notificar',
                'enviados': 0,
                'fallidos': 0,
                'detalle': [],
            }
        asunto = f'Materia cerrada — {materia.nombre} ({materia.nrc})'
        detalle: List[Dict[str, Any]] = []
        enviados = 0
        fallidos = 0

        def _enviar_uno(alumno):
            context = {
                'alumno_nombre': alumno.nombre,
                'matricula': alumno.matricula,
                'materia_nombre': materia.nombre,
                'nrc': materia.nrc,
                'seccion': materia.seccion,
                'periodo_nombre': materia.periodo_nombre,
                'login_url': self.frontend_url,
            }
            try:
                html = self.templates.render_cierre_materia(context)
            except Exception as exc:
                reg = self._fail(
                    TipoCorreo.CIERRE_MATERIA,
                    alumno.email,
                    asunto,
                    '',
                    f'Error al renderizar: {exc}',
                )
                return reg
            return self._send(
                tipo=TipoCorreo.CIERRE_MATERIA,
                to_email=alumno.email,
                asunto=asunto,
                html_body=html,
            )

        workers = min(self.max_workers, max(len(alumnos), 1))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_enviar_uno, a): a for a in alumnos}
            for future in as_completed(futures):
                result = future.result()
                detalle.append(result)
                if result.get('success'):
                    enviados += 1
                else:
                    fallidos += 1

        success = fallidos == 0
        return {
            'success': success,
            'message': f'Enviados: {enviados}, fallidos: {fallidos}',
            'enviados': enviados,
            'fallidos': fallidos,
            'detalle': detalle,
        }

    def send_reset_password(
        self, email: str, token: str, reset_url: str
    ) -> Dict[str, Any]:
        if not email or not reset_url:
            return self._fail(
                TipoCorreo.RESET_PASSWORD,
                email or '',
                'Restablece tu contraseña AGM',
                '',
                'email y reset_url son obligatorios',
            )
        asunto = 'Restablece tu contraseña — AGM'
        context = {
            'reset_url': reset_url,
            'frontend_url': self.frontend_url,
        }
        try:
            html = self.templates.render_reset_password(context)
        except Exception as exc:
            return self._fail(
                TipoCorreo.RESET_PASSWORD,
                email,
                asunto,
                '',
                f'Error al renderizar plantilla: {exc}',
            )
        return self._send(
            tipo=TipoCorreo.RESET_PASSWORD,
            to_email=email,
            asunto=asunto,
            html_body=html,
        )

    def _send(
        self,
        *,
        tipo: str,
        to_email: str,
        asunto: str,
        html_body: str,
    ) -> Dict[str, Any]:
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
            registro = self.historial.registrar(
                tipo=tipo,
                destinatario_email=to_email,
                asunto=asunto,
                cuerpo=html_body,
                exitoso=True,
            )
            return {
                'success': True,
                'message': 'Correo enviado',
                'historial_id': registro.id,
                'destinatario_email': to_email,
            }
        except Exception as exc:
            logger.exception('Fallo SMTP tipo=%s dest=%s', tipo, to_email)
            registro = self.historial.registrar(
                tipo=tipo,
                destinatario_email=to_email,
                asunto=asunto,
                cuerpo=html_body,
                exitoso=False,
                error_msg=str(exc)[:2000],
            )
            return {
                'success': False,
                'message': str(exc),
                'historial_id': registro.id,
                'destinatario_email': to_email,
            }

    def _fail_from_domain(
        self,
        exc: NotificacionesDomainError,
        tipo: str,
        asunto: str,
        to_email: str = '',
    ) -> Dict[str, Any]:
        if isinstance(exc, UpstreamUnavailable):
            logger.warning('Upstream no disponible: %s', exc)
        elif isinstance(exc, UpstreamGrpcError):
            logger.error('Error gRPC upstream: %s', exc)
        return self._fail(tipo, to_email, asunto, '', str(exc))

    def _fail(
        self,
        tipo: str,
        to_email: str,
        asunto: str,
        html_body: str,
        error_msg: str,
    ) -> Dict[str, Any]:
        registro = self.historial.registrar(
            tipo=tipo,
            destinatario_email=to_email or 'desconocido@agm.local',
            asunto=asunto or 'Error',
            cuerpo=html_body,
            exitoso=False,
            error_msg=error_msg,
        )
        return {
            'success': False,
            'message': error_msg,
            'historial_id': registro.id,
            'destinatario_email': to_email,
        }
