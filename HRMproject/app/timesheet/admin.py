from django.contrib import admin
from .models import Timesheet, WorkType,CommendationDiscipline,LeaveRequest,AllowanceType,Overtime,ShiftType,SalaryAdvance
# Register your models here.
admin.site.register(Timesheet)
admin.site.register(WorkType)
admin.site.register(CommendationDiscipline)
admin.site.register(LeaveRequest)
admin.site.register(AllowanceType)
admin.site.register(Overtime)
admin.site.register(ShiftType)
admin.site.register(SalaryAdvance)