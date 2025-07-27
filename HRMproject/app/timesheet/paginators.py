from rest_framework import pagination

class TimesheetPagination(pagination.PageNumberPagination):
    page_size = 31