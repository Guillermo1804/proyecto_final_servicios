"""Endpoints de claves publicas para validacion JWT local."""

from __future__ import annotations

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apps.core.jwt_keys import build_jwks_document, get_rsa_public_key_pem


@api_view(["GET"])
@permission_classes([AllowAny])
def jwks(request):
    """
    GET /.well-known/jwks.json
    Claves publicas para validar JWT emitidos por MS-1 (RS256).
    """
    if getattr(settings, "JWT_ALGORITHM", "HS256") != "RS256":
        return JsonResponse(
            {
                "success": False,
                "message": "JWKS disponible solo con JWT_ALGORITHM=RS256",
            },
            status=503,
        )
    return JsonResponse(build_jwks_document())


@api_view(["GET"])
@permission_classes([AllowAny])
def public_key_pem(request):
    """
    GET /.well-known/jwt-public.pem
    Alternativa legible a JWKS para herramientas que consumen PEM.
    """
    if getattr(settings, "JWT_ALGORITHM", "HS256") != "RS256":
        return JsonResponse(
            {"success": False, "message": "Clave publica no disponible para HS256"},
            status=503,
        )
    return HttpResponse(get_rsa_public_key_pem(), content_type="application/x-pem-file")
