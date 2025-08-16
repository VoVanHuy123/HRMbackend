from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from django_mysql.models import EnumField


class UserRole(models.TextChoices):
    ADMIN = 'Admin', 'Admin'
    EMPLOYEE = 'Employee', 'Employee'


class User(AbstractUser):
    avatar = CloudinaryField(blank=True, null=True)
    role = EnumField(choices=UserRole.choices, default=UserRole.EMPLOYEE)
    is_first_access = models.BooleanField(default=True)
    employee = models.OneToOneField("employee.Employee", on_delete=models.SET_NULL, null=True, blank=True, related_name='user_account', verbose_name="employee.Employee")

    class Meta:
        db_table = "user"