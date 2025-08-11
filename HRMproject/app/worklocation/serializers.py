from rest_framework import serializers
from.models import WorkLocation
from employee.serializers import NameEmployeeSerializer

class CreateWorkLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLocation
        fields = ["employee","date","description",'latitude','longitude','name']
class WorkLocationSerializer(serializers.ModelSerializer):
    employee = NameEmployeeSerializer()
    class Meta:
        model = WorkLocation
        fields = ["employee","date","description",'latitude','longitude','name']

