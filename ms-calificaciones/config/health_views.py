from django.http import JsonResponse
from decouple import config


def health(request):
    return JsonResponse({
        'status': 'ok',
        'service': config('SERVICE_NAME', default='ms-auth'),
    })
