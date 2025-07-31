from django_filters import rest_framework as filters
from .models import *
from django.db.models import Value, CharField
from django.db.models.functions import Concat

class PayrollFilter(filters.FilterSet):
    month = filters.NumberFilter(field_name="month", lookup_expr="exact")
    year = filters.NumberFilter(field_name="year", lookup_expr="exact")
    name = filters.CharFilter(method='filter_name', label='Employee name')
    employee_id = filters.NumberFilter(field_name='employee__id', lookup_expr='exact')

    def filter_name(self, queryset, name, value):
        return queryset.annotate(
            full_name=Concat(
                'employee__first_name',
                Value(' '),
                'employee__last_name',
                output_field=CharField()
            )
        ).filter(full_name__icontains=value)

    class Meta:
        model =  Payroll
        fields = [ 'month', 'year', 'name', 'employee_id']