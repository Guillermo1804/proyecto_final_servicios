"""Propaga X-Correlation-Id desde peticiones HTTP."""

from __future__ import annotations

import uuid

from django.utils.deprecation import MiddlewareMixin

from apps.core.event_bus.context import reset_correlation_id, set_correlation_id


class CorrelationIdMiddleware(MiddlewareMixin):
    HEADER = "HTTP_X_CORRELATION_ID"

    def process_request(self, request):
        incoming = request.META.get(self.HEADER)
        correlation_id = incoming.strip() if incoming else str(uuid.uuid4())
        request.correlation_id = correlation_id
        request._correlation_token = set_correlation_id(correlation_id)

    def process_response(self, request, response):
        correlation_id = getattr(request, "correlation_id", None)
        if correlation_id:
            response["X-Correlation-Id"] = correlation_id
        token = getattr(request, "_correlation_token", None)
        if token is not None:
            reset_correlation_id(token)
        return response
