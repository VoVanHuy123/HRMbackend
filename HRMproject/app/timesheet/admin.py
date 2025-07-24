from django.contrib import admin
from .models import Timesheet, WorkType,CommendationDiscipline,LeaveRequest
# Register your models here.
admin.site.register(Timesheet)
admin.site.register(WorkType)
admin.site.register(CommendationDiscipline)
admin.site.register(LeaveRequest)