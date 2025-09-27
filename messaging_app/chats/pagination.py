# messaging_app/chats/pagination.py
from rest_framework.pagination import PageNumberPagination

class DefaultPagination(PageNumberPagination):
    page_size = 20  # default per page
    page_size_query_param = "page_size"
    max_page_size = 100
