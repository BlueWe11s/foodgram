from rest_framework.pagination import PageNumberPagination

from recipes.constants import PAGE_SIZE


class Pagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = PAGE_SIZE