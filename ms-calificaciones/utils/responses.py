from rest_framework.response import Response


def success_response(data, message='OK', status=200):
    return Response(
        {'success': True, 'data': data, 'message': message},
        status=status,
    )


def error_response(message, errors=None, status=400):
    return Response(
        {
            'success': False,
            'data': None,
            'message': message,
            'errors': errors or {},
        },
        status=status,
    )
