from datetime import datetime

from django.utils import timezone
from rest_framework.response import Response


def format_data_as_of(value: datetime | None) -> str:
    if value is None:
        return ''
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return value.isoformat()


def success_response(
    data,
    message='OK',
    status=200,
    pagination=None,
    *,
    data_as_of: datetime | None = None,
):
    """Envelope estándar para respuestas exitosas."""
    if isinstance(data, dict) and data_as_of is not None:
        data = {**data, 'data_as_of': format_data_as_of(data_as_of)}
    body = {'success': True, 'data': data, 'message': message}
    if pagination:
        body['pagination'] = pagination
    response = Response(body, status=status)
    if data_as_of is not None:
        response['X-AGM-Data-As-Of'] = format_data_as_of(data_as_of)
    return response


def error_response(message, errors=None, status=400):
    """Envelope estándar para respuestas de error."""
    return Response(
        {
            'success': False,
            'data': None,
            'message': message,
            'errors': errors or {},
        },
        status=status,
    )
