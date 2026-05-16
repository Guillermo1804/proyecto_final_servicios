from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class AGMPagination(PageNumberPagination):
    """Paginación estándar del proyecto AGM con envelope para MS-3."""
    page_size = 10
    page_query_param = "page"
    page_size_query_param = "limit"
    max_page_size = 100

    def get_paginated_response(self, data):
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
