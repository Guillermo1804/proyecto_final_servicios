import logging

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view

from apps.core.models import EstadoMateria
from utils.notificaciones_client import send_cierre_materia
from utils.responses import error_response, success_response

logger = logging.getLogger(__name__)


@api_view(['POST'])
def cerrar_materia(request, materia_id: int):
    """
    POST /materias/<id>/cerrar
    Marca la materia como cerrada y dispara notificación masiva en MS-6.
    """
    if materia_id <= 0:
        return error_response('materia_id inválido', status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            estado, _ = EstadoMateria.objects.select_for_update().get_or_create(
                materia_id=materia_id,
                defaults={'cerrada': False},
            )
            if estado.cerrada:
                return error_response('La materia ya está cerrada', status=status.HTTP_400_BAD_REQUEST)

            estado.cerrada = True
            estado.fecha_cierre = timezone.now()
            estado.save(update_fields=['cerrada', 'fecha_cierre'])

        notificacion_ok = send_cierre_materia(materia_id)
        if notificacion_ok:
            EstadoMateria.objects.filter(materia_id=materia_id).update(notificacion_enviada=True)

        return success_response(
            {
                'materia_id': materia_id,
                'cerrada': True,
                'notificacion_enviada': notificacion_ok,
            },
            message='Materia cerrada correctamente',
            status=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.exception('Error al cerrar materia %s', materia_id)
        return error_response(f'Error al cerrar materia: {exc}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
