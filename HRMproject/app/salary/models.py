from django.db import models
from HRMproject.models import BaseModel
from employee.models import Employee

# Create your models here.
class BaseSalary(BaseModel):
    salary = models.BigIntegerField(default=0.0,unique=True)

    def __str__(self):
        return f"Lương cơ bản: {self.salary} VND"

class WorkStandard(BaseModel):
    standard_work_number = models.IntegerField(unique=True)

    def __str__(self):
        return f"Công chuẩn: {self.standard_work_number} ngày"
    class Meta:
        ordering = ["standard_work_number"]
        
# Bảng lương tổng hợp hàng tháng
class Payroll(BaseModel):
    employee = models.ForeignKey('employee.Employee', on_delete=models.CASCADE,null=True, blank=True, related_name='payrolls',)
    month = models.IntegerField()
    year = models.IntegerField()
    working_day = models.FloatField()
    # standard_work_number = models.ForeignKey(WorkStandard, on_delete=models.SET_NULL, null=True)
    standard_work_number = models.IntegerField(default=0)
    coefficient = models.FloatField(default=0.0)
    base_salary = models.FloatField(default=0.0)
    overtime_pay = models.FloatField(default=0.0)
    bonus = models.FloatField(default=0.0)
    penalty = models.FloatField(default=0.0)
    allowance = models.FloatField(default=0.0)
    is_locked = models.BooleanField(default=False)
    
    
    # Các trường tự động tính
    actual_salary = models.BigIntegerField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')
    
    def save(self, *args, **kwargs):
        self.coefficient = self.employee.salary_grade.coefficient
        self.base_salary = self.employee.base_salary.salary
        # if self.date:
        #     self.month = self.date.month
        #     self.year = self.date.year
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Lương {self.month}/{self.year} - {self.employee}"
class PayrollHistory(models.Model):
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)
    updated_by = models.ForeignKey("employee.Employee", on_delete=models.SET_NULL, null=True)
    data = models.JSONField()  # Hoặc TextField nếu bạn dùng string hóa
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lịch sử - {self.payroll.employee} {self.timestamp.strftime('%d-%m-%Y %H:%M')}"
class SalaryGrade(BaseModel):
    grade_name = models.CharField(max_length=255,unique=True)
    coefficient = models.FloatField(default=0.0)
    description = models.TextField()