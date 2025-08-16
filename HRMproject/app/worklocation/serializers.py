from rest_framework import serializers
from.models import WorkLocation,OfficeLocation
from employee.serializers import NameEmployeeSerializer

class CreateWorkLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLocation
        fields = ["id","employee","date","description",'latitude','longitude','name']
class WorkLocationSerializer(serializers.ModelSerializer):
    employee = NameEmployeeSerializer()
    class Meta:
        model = WorkLocation
        fields = ["id","employee","date","description",'latitude','longitude','name',"status"]
class UpdateWorkLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLocation
        fields = ["id","date","description",'name',"status"]

class OfficeLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficeLocation
        fields = ['id','name','address','latitude','longitude']
