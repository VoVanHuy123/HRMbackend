from django_filters import rest_framework as filters
from .models import *
from employee.models import EmployeeAllowance
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from HRMproject.filters import BaseFilter



class LeaveRequestFilter(filters.FilterSet):
     # Lọc theo ngày nghỉ
    date = filters.DateFilter(field_name='date', lookup_expr='exact')
    
    # Lọc theo status
    status = filters.CharFilter(field_name='status', lookup_expr='exact')
    
    # Lọc theo họ tên nhân viên (first_name + last_name)
    name = filters.CharFilter(method='filter_name', label='Employee name')

    employee_id = filters.NumberFilter(field_name='employee__id', lookup_expr='exact')
    month = filters.NumberFilter(method='filter_month')
    year = filters.NumberFilter(method='filter_year')

    class Meta:
        model = LeaveRequest
        fields = ['date', 'status', 'name',"employee_id","month","year"]

    def filter_name(self, queryset, name, value):
        return queryset.annotate(
            full_name=Concat(
                'employee__first_name',
                Value(' '),
                'employee__last_name',
                output_field=CharField()
            )
        ).filter(full_name__icontains=value)
    def filter_month(self, queryset, name, value):
        return queryset.filter(date__month=value)

    def filter_year(self, queryset, name, value):
        return queryset.filter(date__year=value)

class TimesheetFilter(filters.FilterSet):
    day = filters.NumberFilter(field_name="date", lookup_expr="day")
    month = filters.NumberFilter(field_name="month", lookup_expr="exact")
    year = filters.NumberFilter(field_name="year", lookup_expr="exact")

    name = filters.CharFilter(method='filter_name', label='Employee name')
    employee_id = filters.NumberFilter(field_name='employee__id', lookup_expr='exact')
    class Meta:
        model = Timesheet
        fields = ['day', 'month', 'year',"name","employee_id"]

    def filter_name(self, queryset, name, value):
        return queryset.annotate(
            full_name=Concat(
                'employee__first_name',
                Value(' '),
                'employee__last_name',
                output_field=CharField()
            )
        ).filter(full_name__icontains=value)
    
class OverTimeFilter(BaseFilter):
    class Meta(BaseFilter.Meta):
        model = Overtime
        fields = BaseFilter.Meta.fields
class SalaryAdvanceFilter(BaseFilter):
    class Meta(BaseFilter.Meta):
        model = SalaryAdvance
        fields = BaseFilter.Meta.fields
class EmployeeAllowanceFilter(BaseFilter):
    class Meta(BaseFilter.Meta):
        model = EmployeeAllowance
        fields = BaseFilter.Meta.fields

class CommendationDisciplineFilter(BaseFilter):
    class Meta(BaseFilter.Meta):
        model = CommendationDiscipline
        fields = BaseFilter.Meta.fields

class AllowanceTypeFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    class Meta:
        model = AllowanceType
        fields = ["name"]