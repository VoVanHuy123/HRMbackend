from django.db import models
from HRMproject.models import BaseModel
from cloudinary.models import CloudinaryField
from django.core.validators import RegexValidator

# Create your models here.
class Employee(BaseModel):
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    last_name = models.CharField(max_length=100, verbose_name="Last Name")
    gender = models.CharField(max_length=10, verbose_name="Gender") # e.g., 'Male', 'Female', 'Other'
    date_of_birth = models.DateField(verbose_name="Date of Birth")
    
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10, unique=True, validators=[
        RegexValidator(
            regex=r'^\d{10}$',
            message='Số điện thoại phải đúng 10 chữ số',
        )
    ])
    citizen_id = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Citizen ID/Passport")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Address")
    photo = CloudinaryField(blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True, verbose_name="Email")

    # Foreign Keys
    qualification = models.ForeignKey("Qualification", on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="Qualification")
    position = models.ForeignKey("Position", on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="Position")
    department = models.ForeignKey("Department", on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="Department")
    division = models.ForeignKey("Division", on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="Division")
    salary_grade = models.ForeignKey("salary.SalaryGrade",on_delete=models.SET_NULL,null=True,
        blank=True,
        related_name="employees",
        verbose_name="Salary Grade"
    )
    base_salary = models.ForeignKey("salary.BaseSalary",on_delete=models.SET_NULL,null=True, blank=True, related_name='employees', verbose_name="BaseSalary")
    

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        db_table = "Employee"
        ordering = ['-id']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

# Vị Trí/ chức vụ
class Position(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="Position Name")

    class Meta:
        verbose_name = "Position"
        verbose_name_plural = "Positions"
        db_table = "position"

    def __str__(self):
        return self.name


# Phòng ban
class Department(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="Department Name")
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        db_table = "department"

    def __str__(self):
        return self.name


# Bộ phận
class Division(BaseModel):
    name = models.CharField(max_length=255, verbose_name="Division Name")
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="divisions",
        verbose_name="Department",
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name = "Division"
        verbose_name_plural = "Divisions"
        db_table = "division"
        unique_together = ("department", "name")  # hoặc dùng UniqueConstraint

    def __str__(self):
        return self.name


# Hợp đồng
class Contract(BaseModel):
    employee = models.OneToOneField("Employee", on_delete=models.CASCADE, primary_key=True, related_name='contract', verbose_name="Employee")
    contract_number = models.CharField(max_length=50, unique=True, verbose_name="Contract Number")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date") # Can be open-ended
    contract_type = models.CharField(max_length=100, verbose_name="Contract Type") # e.g., 'Internship', 'Probationary', 'Official'
    signing_count = models.IntegerField(verbose_name="Signing Count") # Number of times signed
    duration = models.CharField(max_length=50, verbose_name="Duration") # e.g., '1 year', 'Indefinite'
    # salary_coefficient = models.FloatField(verbose_name="Salary Coefficient")

    class Meta:
        verbose_name = "Contract"
        verbose_name_plural = "Contracts"

    def __str__(self):
        return f"Contract for {self.employee.first_name} {self.employee.last_name} - {self.contract_number}"

# bảo hiểm
class Insurance(BaseModel):
    employee = models.OneToOneField("Employee", on_delete=models.CASCADE, primary_key=True, related_name='insurance', verbose_name="Employee")
    insurance_number = models.CharField(max_length=50, unique=True, verbose_name="Insurance Number")
    issue_date = models.DateField(verbose_name="Issue Date")
    issue_place = models.CharField(max_length=255, verbose_name="Issue Place")
    medical_examination_place = models.CharField(max_length=255, blank=True, null=True, verbose_name="Medical Examination Place")

    class Meta:
        verbose_name = "Insurance"
        verbose_name_plural = "Insurance Records"
        db_table = "insurance"

    def __str__(self):
        return f"Insurance for {self.employee.first_name} {self.employee.last_name} - {self.insurance_number}"

# Nhân viên - Phụ Cấp
class EmployeeAllowance(BaseModel):
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE, related_name='employee_allowances', verbose_name="Employee")
    allowance_type = models.ForeignKey("timesheet.AllowanceType", on_delete=models.CASCADE, related_name='employee_allowances', verbose_name="Allowance Type")
    date = models.DateField(verbose_name="Date")
    content = models.TextField(blank=True, null=True, verbose_name="Content")
    amount = models.FloatField(verbose_name="Amount")

    class Meta:
        verbose_name = "Employee Allowance"
        verbose_name_plural = "Employee Allowances"
        unique_together = ('employee', 'allowance_type', 'date') # An employee can have a specific allowance once per day
        db_table = "employee_allowance"

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} - {self.allowance_type.name} ({self.date})"
    
# Trình độ
class Qualification(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="Qualification Name")

    class Meta:
        verbose_name = "Qualification"
        verbose_name_plural = "Qualifications"

    def __str__(self):
        return self.name

