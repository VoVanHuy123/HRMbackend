from rest_framework import pagination

class PayRollPagination(pagination.PageNumberPagination):
    page_size = 31