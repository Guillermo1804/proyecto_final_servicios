from rest_framework.views import exception_handler as drf_exception_handler

from utils.responses import error_response


def agm_exception_handler(exc, context):
    """Envuelve respuestas DRF en el envelope AGM."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    message = 'Error'
    errors = {}
    data = response.data
    if isinstance(data, dict):
        if 'detail' in data:
            message = str(data['detail'])
        else:
            message = 'Error de validación'
            errors = data
    elif isinstance(data, list):
        message = str(data[0]) if data else message
    else:
        message = str(data)
    return error_response(message, errors=errors, status=response.status_code)
