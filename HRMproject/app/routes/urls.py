from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user.views import UserViewSet
from employee.views import *
from salary.views import BaseSalaryViewset,SalaryGradeViewset,PayrollViewset,WorkStandardViewset
from timesheet.views import *


routers = DefaultRouter()
routers.register('users', UserViewSet, basename='user')
routers.register('employees', EmployeeViewset, basename='employee')
routers.register('contracts',ContractViewset,basename='contract')
routers.register('departments',DepartmentViewset,basename="department")
routers.register('divisions',DivisionViewset,basename="division")
routers.register('qualifications',QualificationViewset,basename="qualification")
routers.register('positions',PositionViewset,basename="position")
routers.register('base_salarys',BaseSalaryViewset,basename="base_salary")
routers.register('salary_grades',SalaryGradeViewset,basename="salary_grade")
routers.register('commendations_disciplines',CommendationDisciplineViewsets,basename="commendation_discipline")
routers.register('leave_requests',LeaveRequestViewset,basename="leave_request")
routers.register('time_sheets',TimeSheetViewset,basename="time_sheet")
routers.register('work_types',WorkTypeViewset,basename="work_type")
routers.register('over_times',OverTimeViewset,basename="over_time")
routers.register('salary_advances',SalaryAdvanceViewset,basename="salary_advance")
routers.register('allowance_types',AllowanceTypeViewset,basename="allowance_type")
routers.register('employee_allowances',EmployeeAllowanceViewset,basename="employee_allowance")
routers.register('shift_types',ShiftTypeViewset,basename="shift_type")
routers.register('payrolls',PayrollViewset,basename="payroll")
routers.register('work_standards',WorkStandardViewset,basename="work_standard")
routers.register('insurances',InsuranceViewset,basename="insurance")
urlpatterns = [
    path('', include(routers.urls)),

]