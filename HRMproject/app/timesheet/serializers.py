from rest_framework import serializers
from .models import (
    Timesheet,WorkType,
    CommendationDiscipline,
    LeaveRequest,
    Overtime,
    SalaryAdvance,
    AllowanceType,
    ShiftType
    )
from employee.models import (
    EmployeeAllowance,
)
from employee.serializers import NameEmployeeSerializer


class WorkTypeserializer(serializers.ModelSerializer):
    class Meta:
        model = WorkType
        fields = ["id","name","coefficient"]
class TimeSheetEmployeeSerializers(serializers.ModelSerializer):
    work_type = WorkTypeserializer()
    employee = NameEmployeeSerializer()
    class Meta:
        model = Timesheet
        # fields = "__all__"
        fields = ["id","date","employee","year","month","time_in","time_out","total_working_hours","work_coefficient","work_type"]
class TimeSheetSerializers(serializers.ModelSerializer):
    work_type = WorkTypeserializer()
    class Meta:
        model = Timesheet
        # fields = "__all__"
        fields = ["id","date","year","month","time_in","time_out","total_working_hours","work_coefficient","work_type"]
class UpdateTimeSheetSerializers(serializers.ModelSerializer):
    class Meta:
        model = Timesheet
        # fields = "__all__"
        fields = ["id","date","year","month","time_in","time_out","total_working_hours","work_coefficient","work_type"]

class CommendationDisciplineSerializers(serializers.ModelSerializer):
    employee = NameEmployeeSerializer()
    class Meta:
        model = CommendationDiscipline
        fields = ['id', 'employee', 'content', 'date', 'record_type', 'amount']
class UpdateCommendationDisciplineSerializers(serializers.ModelSerializer):
    class Meta:
        model = CommendationDiscipline
        fields = ['id', 'content', 'date', 'record_type', 'amount']
class LeaveRequestSerializers(serializers.ModelSerializer):
    employee = NameEmployeeSerializer()
    class Meta:
        model = LeaveRequest
        fields = ['id','content','date','status','employee']
class CreateLeaveRequestSerializers(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['id','content','date','employee',"status"]
class ShifTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftType
        fields = ["id","name","coefficient"]
class OverTimeSerializers(serializers.ModelSerializer):
    employee = NameEmployeeSerializer()
    shift_type = ShifTypeSerializer()
    class Meta:
        model = Overtime
        fields = ['id','hours','date','time_in','time_out','employee',"shift_type"]
class createTimeSerializers(serializers.ModelSerializer):
    class Meta:
        model = Overtime
        fields = ['id','month','date','year','time_in','time_out','employee',"shift_type"]
class UpdateOverTimeSerializers(serializers.ModelSerializer):
    class Meta:
        model = Overtime
        fields = ['id','month','date','year','time_in','time_out',"shift_type"]
class SalaryAdvanceSerializers(serializers.ModelSerializer):
    employee = NameEmployeeSerializer()
    class Meta:
        model = SalaryAdvance
        fields = ['id','month','date','year','status','amount','employee']
class CreateSalaryAdvanceSerializers(serializers.ModelSerializer):
    class Meta:
        model = SalaryAdvance
        fields = ['id','date','amount','status','employee']
class UpdateSalaryAdvanceSerializers(serializers.ModelSerializer):
    class Meta:
        model = SalaryAdvance
        fields = ['id','month','date','year','status','amount']
class AllowanceTypeSerializer(serializers.ModelSerializer):
    class Meta: 
        model = AllowanceType
        fields = ["id","name","amount","is_fixed"]
class EmployeeAllowanceSerializer(serializers.ModelSerializer):
    employee = NameEmployeeSerializer()
    allowance_type = AllowanceTypeSerializer()
    class Meta: 
        model = EmployeeAllowance
        fields = ["id","employee","allowance_type","date","content","amount"]
class UpdateEmployeeAllowanceSerializer(serializers.ModelSerializer):
    class Meta: 
        model = EmployeeAllowance
        fields = ["id","date","content","amount","allowance_type"]
class CreateEmployeeAllowanceSerializer(serializers.ModelSerializer):
    class Meta: 
        model = EmployeeAllowance
        fields = ["id","employee","allowance_type","date","content","amount"]
