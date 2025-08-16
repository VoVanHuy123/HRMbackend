from rest_framework import serializers
from .models import BaseSalary,SalaryGrade,WorkStandard,Payroll
from employee.serializers import NameEmployeeSerializer


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
    employee = NameEmployeeSerializer(read_only=True)
    class Meta:
        model = Payroll
        fields = ["id","employee","month","year","working_day",
                  "standard_work_number","coefficient","base_salary",
                  "overtime_pay","bonus","penalty","allowance","actual_salary","note"]
        read_only_fields = (
            "employee", "coefficient", "base_salary",
            "overtime_pay", "bonus", "penalty", "allowance",
            "actual_salary"
        )
class UpdatePayRollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = [
            "id", "month", "year", "working_day",
            "standard_work_number", "note"
        ]
class CreatePayRollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = [
            "id", "employee", "month", "year",
            "standard_work_number", "note"
        ]
        extra_kwargs = {
            "id": {"read_only": True}
        }