from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user.views import UserViewSet
from employee.views import EmployeeViewset,ContractViewset,DepartmentViewset,DivisionViewset,QualificationViewset,PositionViewset
from salary.views import BaseSalaryViewset,SalaryGradeViewset
from timesheet.views import CommendationDisciplineViewsets , LeaveRequestViewset


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
urlpatterns = [
    path('', include(routers.urls)),

]