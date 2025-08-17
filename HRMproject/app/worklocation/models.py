from django.db import models
from employee.models import Employee
from HRMproject.models import BaseModel
from django.utils import timezone
from timesheet.models import StatusType
# from django_mysql.models import EnumField
from datetime import datetime

# Create your models here.

class WorkLocation(BaseModel):
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE, related_name='work_locations', verbose_name="Employee")
    date = models.DateField(verbose_name="Date", null=True, default=datetime.now)
    name = models.CharField(max_length=255,null=True,blank=True)  # Tên địa điểm (VD: Văn phòng HCM)
    description = models.CharField(max_length=255,null=True,blank=True)  # Tên địa điểm (VD: Văn phòng HCM)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)  # Vĩ độ
    longitude = models.DecimalField(max_digits=9, decimal_places=6)  # Kinh độ
    # status = EnumField(choices=StatusType.choices, default=StatusType.PENDING)
    status = models.CharField(
        max_length=20,
        choices=StatusType.choices,
        default=StatusType.PENDING
    )
    # radius = models.IntegerField(default=100)  # Bán kính cho phép (m)

    class Meta:
        unique_together = ("employee", 'date')

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name}- {self.name}"

class OfficeLocation(BaseModel):
    name = models.CharField(max_length=255,null=True,blank=True)  # Tên địa điểm (VD: Văn phòng HCM)
    address = models.CharField(max_length=255,null=True,blank=True)  # Tên địa điểm (VD: Văn phòng HCM)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)  # Vĩ độ
    longitude = models.DecimalField(max_digits=9, decimal_places=6)  # Kinh độ

    def __str__(self):
        return f"{self.name} - {self.address}"