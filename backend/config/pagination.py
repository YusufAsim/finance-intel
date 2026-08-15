"""Pagination shared by every list endpoint."""

from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Page size is caller controlled, with a ceiling."""

    page_size_query_param = "page_size"
    max_page_size = 500
