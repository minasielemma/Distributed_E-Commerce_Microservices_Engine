import math
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        count = self.page.paginator.count
        page_size = self.get_page_size(self.request)
        total_pages = math.ceil(count / page_size) if page_size and page_size > 0 else 1

        return Response({
            'count': count,
            'total_pages': total_pages,
            'current_page': self.page.number,
            'page_size': page_size,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
