from rest_framework import serializers
from .models import Timesheet,WorkType,CommendationDiscipline,LeaveRequest


class WorkTypeserializer(serializers.ModelSerializer):
    class Meta:
        model = WorkType
        fields = ["id","name","coefficient"]
class TimeSheetSerializers(serializers.ModelSerializer):
    work_type = WorkTypeserializer()
    class Meta:
        model = Timesheet
        # fields = "__all__"
        fields = ["id","date","year","month","time_in","time_out","total_working_hours","work_type"]

class CommendationDisciplineSerializers(serializers.ModelSerializer):
    class Meta:
        model = CommendationDiscipline
        fields = ['id', 'employee', 'content', 'date', 'record_type', 'amount']
class LeaveRequestSerializers(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['id','content','date','status','employee']