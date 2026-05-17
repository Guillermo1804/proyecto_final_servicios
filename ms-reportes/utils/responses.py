from rest_framework.response import Response


def success_response(data, message='OK', status=200, pagination=None):
    """Envelope estándar para respuestas exitosas."""
    body = {'success': True, 'data': data, 'message': message}
    if pagination:
        body['pagination'] = pagination
    return Response(body, status=status)


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
