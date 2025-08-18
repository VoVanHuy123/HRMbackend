from rest_framework import serializers
from .models import Employee,Contract,Department,Division,Qualification,Position,Insurance
from salary.models import SalaryGrade,BaseSalary
class EmployeeSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    def to_representation(self, instance):
            data = super().to_representation(instance)

            # Nếu instance.photo là object Cloudinary
            if hasattr(instance.photo, 'url'):
                data['photo'] = instance.photo.url
            else:
                # Nếu là string (link cloudinary) hoặc None
                data['photo'] = instance.photo if instance.photo else ''
            
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

class OfficeEmployeeSerializer(serializers.ModelSerializer):
    qualification = serializers.PrimaryKeyRelatedField(queryset=Qualification.objects.all(), required=False)
    position = serializers.PrimaryKeyRelatedField(queryset=Position.objects.all(), required=False)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), required=False)
    division = serializers.PrimaryKeyRelatedField(queryset=Division.objects.all(), required=False)
    salary_grade = serializers.PrimaryKeyRelatedField(queryset=SalaryGrade.objects.all(), required=False)
    base_salary = serializers.PrimaryKeyRelatedField(queryset=BaseSalary.objects.all(), required=False)
    class Meta:
        model = Employee
        fields = ["id",
                  'qualification',
                  'position',
                  'department',
                  'division',
                  "salary_grade",
                  "base_salary",
                  ]
class UpdateEmployeeSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    def to_representation(self, instance):
            data = super().to_representation(instance)

            photo = instance.photo

            if not photo:
                data['photo'] = ''
            elif hasattr(photo, 'url'):
                data['photo'] = photo.url   # Trường hợp Cloudinary object
            else:
                data['photo'] = str(photo)  # Trường hợp đã là string URL

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
                  "active"
                  ]
        extra_kwargs ={
            "citizen_id":{'required':False},
            "email":{'required':False},
            "first_name":{'required':False},
            "last_name":{'required':False},
            "date_of_birth":{'required':False},
            "phone_number":{'required':False},
            "email":{'required':False},
        }
        

class ListEmployeeSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
            data = super().to_representation(instance)

            # Nếu instance.photo là object Cloudinary
            if hasattr(instance.photo, 'url'):
                data['photo'] = instance.photo.url
            else:
                # Nếu là string (link cloudinary) hoặc None
                data['photo'] = instance.photo if instance.photo else ''
            
            return data
    class Meta:
        model = Employee
        fields = ["id",'first_name',"last_name","phone_number","email","photo"]
class NameEmployeeSerializer(serializers.ModelSerializer):
    # def to_representation(self, instance):
    #         data = super().to_representation(instance)

    #         data['photo'] = instance.photo.url if instance.photo else ''

    #         return data
    class Meta:
        model = Employee
        fields = ["id",'first_name',"last_name"]

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
        fields = ["id","name","description"]
class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = ["id","name",]
class QualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qualification
        fields = ["id","name",]
class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["id","name",]
class InsuranceSerializer(serializers.ModelSerializer):
    employee = NameEmployeeSerializer()
    class Meta:
        model = Insurance
        fields = ["employee","insurance_number","issue_date","issue_place","medical_examination_place"]
class CreateInsuranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insurance
        fields = ["employee","insurance_number","issue_date","issue_place","medical_examination_place"]