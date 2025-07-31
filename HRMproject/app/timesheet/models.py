from django.db import models
from HRMproject.models import BaseModel
from django_mysql.models import EnumField
from datetime import datetime, timedelta

# Create your models here.
#  bảng công
class Timesheet(BaseModel):
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE, related_name='timesheets', verbose_name="Employee")
    year = models.IntegerField(verbose_name="Year")
    month = models.IntegerField(verbose_name="Month")
    date = models.DateField(verbose_name="Date",null=True)
    time_in = models.TimeField(null=True, blank=True, verbose_name="Time In")
    time_out = models.TimeField(null=True, blank=True, verbose_name="Time Out")
    extra_break_minutes = models.IntegerField(default=0, verbose_name="Extra Break Minutes")
    lunch_break = models.IntegerField(default=1)
    total_working_hours = models.FloatField(default=0.0)
    work_coefficient = models.FloatField(default=0.0)

    # Foreign_key
    work_type = models.ForeignKey("WorkType", on_delete=models.SET_NULL, null=True, blank=True, related_name='timesheet', verbose_name="WorkType")

    class Meta:
        verbose_name = "Timesheet"
        verbose_name_plural = "Timesheets"
        unique_together = ("employee", 'date') # An employee can only have one timesheet entry per day
        db_table = 'timesheet'
    def save(self, *args, **kwargs):
        if self.time_in and self.time_out:
            # Combine with date to get datetime objects
            dt_time_in = datetime.combine(self.date, self.time_in)
            dt_time_out = datetime.combine(self.date, self.time_out)
            # Handle overnight shifts
            if dt_time_out < dt_time_in:
                dt_time_out += timedelta(days=1)
            # Calculate total working time in minutes
            worked_minutes = (dt_time_out - dt_time_in).total_seconds() / 60
            # Subtract extra break
            lunch_break_minutes = self.lunch_break * 60
            worked_minutes -= (self.extra_break_minutes + lunch_break_minutes)
            self.total_working_hours = round(worked_minutes / 60, 2)

            coeff = (worked_minutes / 60)/7.5
            if(coeff > 1 ):
                self.work_coefficient = 1
            else:
                self.work_coefficient = round(coeff, 2)
        else:
            self.total_working_hours = 0.0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Timesheet for {self.employee.first_name} {self.employee.last_name} on {self.date}"
    
# loại công
class WorkType(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="Work Coefficient Type Name")
    coefficient = models.FloatField(verbose_name="Coefficient")

    class Meta:
        verbose_name = "Work Type"
        verbose_name_plural = "Work Types"
        db_table = "work_type"

    def __str__(self):
        return self.name

# tăng ca
class Overtime(BaseModel):
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE, related_name='overtimes', verbose_name="Employee")
    date = models.DateField(verbose_name="Date")
    month = models.IntegerField(verbose_name="Month")
    year = models.IntegerField(verbose_name="Year")
    time_in = models.TimeField(null=True, blank=True, verbose_name="Time In")
    time_out = models.TimeField(null=True, blank=True, verbose_name="Time Out")
    hours = models.FloatField(verbose_name="Hours")

    shift_type = models.ForeignKey("ShiftType", on_delete=models.SET_NULL, null=True, blank=True, related_name='overtime', verbose_name="ShiftType")

    class Meta:
        verbose_name = "Overtime"
        verbose_name_plural = "Overtime Records"
        unique_together = ("employee", 'date') # An employee can only have one overtime entry per day
        db_table = "overtime"
    def save(self, *args, **kwargs):
        if self.date:
            self.month = self.date.month
            self.year = self.date.year
        if self.time_in and self.time_out:
            # Combine with date to get datetime objects
            dt_time_in = datetime.combine(self.date, self.time_in)
            dt_time_out = datetime.combine(self.date, self.time_out)
            # Handle overnight shifts
            if dt_time_out < dt_time_in:
                dt_time_out += timedelta(days=1)
            # Calculate total working time in minutes
            worked_minutes = (dt_time_out - dt_time_in).total_seconds() / 60
            self.hours = round(worked_minutes / 60, 2)
        else:
            self.hours = 0.0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Overtime for {self.employee.first_name} {self.employee.last_name} on {self.date}"
# loại ca
class ShiftType(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="Shift Type Name")
    coefficient = models.FloatField(verbose_name="Coefficient")

    class Meta:
        verbose_name = "Shift Type"
        verbose_name_plural = "Shift Types"
        db_table="shift_type"

    def __str__(self):
        return self.name


class RecordType(models.TextChoices):
    COMMENDATION = 'Commendation', 'Commendation'
    DISCIPLINE = 'Discipline', 'Discipline'
# khen thưởng kỷ luật
class CommendationDiscipline(BaseModel):
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE, related_name='commendations_disciplines', verbose_name="Employee")
    # code = models.CharField(max_length=50, unique=True, verbose_name="Record Code") # Assuming a unique code for each record
    content = models.TextField(verbose_name="Content")
    date = models.DateField(verbose_name="Date")
    record_type = EnumField(choices=RecordType.choices, default=RecordType.COMMENDATION)
    amount = models.FloatField(default=0.0)
    class Meta:
        verbose_name = "Commendation/Discipline"
        verbose_name_plural = "Commendations/Disciplines"
        db_table = "commendation_discipline"

    def __str__(self):
        return f"{self.record_type} for {self.employee.first_name} {self.employee.last_name} on {self.date}"

class StatusType(models.TextChoices):
    APPROVED = 'Approved', 'Approved'
    PENDING = 'Pending', 'Pending'
    REJECTED = 'Rejected', 'Rejected'
# Ứng Lương
class SalaryAdvance(BaseModel):
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE, related_name='salary_advances', verbose_name="Employee")
    date = models.DateField(verbose_name="Date")
    month = models.IntegerField(verbose_name="Month",null=True)
    year = models.IntegerField(verbose_name="Year",null=True)
    status = EnumField(choices=StatusType.choices, default=StatusType.PENDING)# e.g., 'Approved', 'Pending'
    amount = models.FloatField(verbose_name="Amount",default=0.0)

    class Meta:
        verbose_name = "Salary Advance"
        verbose_name_plural = "Salary Advances"
        db_table="salary_advance"
    def save(self, *args, **kwargs):
        if self.date:
            self.month = self.date.month
            self.year = self.date.year
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Salary advance for {self.employee.first_name} {self.employee.last_name} on {self.date}"

class AllowanceType(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="Allowance Name")
    amount = models.FloatField(verbose_name="Amount",null=True)
    is_fixed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Allowance Type"
        verbose_name_plural = "Allowance Types"
        db_table = "allowance_type"

    def __str__(self):
        return self.name

class LeaveRequest(BaseModel):
    content = models.TextField()
    date = models.DateField(null=False)
    status = EnumField(choices=StatusType,default=StatusType.PENDING)
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE, related_name="leave_requests")
    
    class Meta:
        unique_together = ("employee", 'date')
    def __str__(self):
        return f"Xin nghỉ - {self.date.strftime('%d/%m/%Y')}" 

