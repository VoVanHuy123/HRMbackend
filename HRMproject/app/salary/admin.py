from django.contrib import admin
from .models import BaseSalary,SalaryGrade,WorkStandard,Payroll,PayrollHistory
# Register your models here.
admin.site.register(BaseSalary)
admin.site.register(SalaryGrade)
admin.site.register(WorkStandard)
admin.site.register(Payroll)
admin.site.register(PayrollHistory)
