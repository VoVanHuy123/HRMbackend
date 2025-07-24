from rest_framework import serializers
from .models import Employee,Contract,Department,Division,Qualification,Position
class EmployeeSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    def to_representation(self, instance):
            data = super().to_representation(instance)

            data['photo'] = instance.photo.url if instance.photo else ''

            return data
    class Meta:
        model = Employee
        
        fields = ["id",
                  'first_name',
                  "last_name",
                  "gender",
                  "date_of_birth",
                  "phone_number",
                  'citizen_id',
                  'address',
                  'email',
                  'photo',
                  'qualification',
                  'position',
                  'department',
                  'division',
                  "salary_grade",
                  "base_salary","active"]
        extra_kwargs ={
            "citizen_id":{'required':True},
            "email":{'required':True}
        }

class ListEmployeeSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
            data = super().to_representation(instance)

            data['photo'] = instance.photo.url if instance.photo else ''

            return data
    class Meta:
        model = Employee
        fields = ["id",'first_name',"last_name","phone_number","email","photo"]

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = [
            "employee",
            "contract_number",
            "start_date",
            "end_date",
            "contract_type",
            "signing_count",
            "duration",
            # "salary_coefficient"
        ]
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id","name"]
class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = ["id","name","department"]
class QualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qualification
        fields = ["id","name",]
class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["id","name",]