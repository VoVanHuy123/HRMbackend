from django_filters import rest_framework as filters
from .models import Employee
from django.db.models import Value, CharField
from django.db.models.functions import Concat

class EmployeeFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_name', label="Search by name")
    id = filters.NumberFilter(field_name='id', lookup_expr='exact')

    class Meta:
        model = Employee
        fields = ['name', 'id']

    def filter_name(self, queryset, name, value):
        # Tạo một annotation tên đầy đủ
        queryset = queryset.annotate(
            full_name=Concat(
                'first_name',
                Value(' '),
                'last_name',
                output_field=CharField()
            )
        )
        return queryset.filter(full_name__icontains=value)
