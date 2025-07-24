from rest_framework import serializers
from .models import BaseSalary,SalaryGrade,WorkStandard,Payroll

class BaseSalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseSalary
        fields = ["id","salary"]
class SalaryGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryGrade
        fields = ["id","grade_name","coefficient","description"]
class WorkStandardSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkStandard
        fields = ["id","standard_work_number"]
class PayRollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = ["__all__"]