from django.contrib import admin
from .models import BaseSalary,SalaryGrade,WorkStandard
# Register your models here.
admin.site.register(BaseSalary)
admin.site.register(SalaryGrade)
admin.site.register(WorkStandard)
