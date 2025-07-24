from rest_framework import pagination

class EmployeePaginator(pagination.PageNumberPagination):
    page_size = 10