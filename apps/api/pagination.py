from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for all API lists.
    - Default page size 20
    - Allow clients to override with `?page_size=` up to 100
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
