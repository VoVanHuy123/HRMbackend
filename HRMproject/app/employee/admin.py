from django.contrib import admin
from .models import Employee,Contract,Position,Department,Division,Insurance,Qualification
# Register your models here.

admin.site.register(Employee)
admin.site.register(Contract)
admin.site.register(Department)
admin.site.register(Division)
admin.site.register(Qualification)
admin.site.register(Position)