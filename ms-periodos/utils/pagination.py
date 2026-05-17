from rest_framework.pagination import PageNumberPagination


class AGMPagination(PageNumberPagination):
    """Paginación estándar del proyecto AGM con envelope."""
    page_size = 10
    page_query_param = "page"
    page_size_query_param = "limit"
    max_page_size = 100

    def get_paginated_envelope(self, data):
        return {
            "success": True,
            "data": data,
            "message": "OK",
            "pagination": {
                "page": self.page.number,
                "total": self.page.paginator.count,
                "limit": self.get_page_size(self.request),
            },
        }

    def get_paginated_response(self, data):
        from rest_framework.response import Response
        return Response({
            "success": True,
            "data": {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            },
            "message": "OK"
        })
