

from django.db.models import Sum
from timesheet.models import AllowanceType
from employee.models import EmployeeAllowance

def get_bonus_penalty(employee, month, year):
    records = employee.commendations_disciplines.filter(
        date__month=month,
        date__year=year
    )
    bonus = records.filter(record_type='Commendation').aggregate(total=Sum('amount'))['total'] or 0
    penalty = records.filter(record_type='Discipline').aggregate(total=Sum('amount'))['total'] or 0
    return bonus, penalty
def get_total_overtime_pay(employee, month, year, work_standard_days):
    overtimes = employee.overtimes.filter(month=month, year=year)

    if not overtimes.exists():
        return 0

    base_salary = employee.base_salary.salary if employee.base_salary else 0
    employee_coe = employee.salary_grade.coefficient if employee.salary_grade else 1

    per_hour_rate = (base_salary / work_standard_days)*employee_coe / 7.5

    total = 0
    for ot in overtimes:
        if ot.shift_type:
            total += per_hour_rate * ot.hours * ot.shift_type.coefficient
        else:
            total += per_hour_rate * ot.hours

    return round(total, 2)
def get_total_allowance(employee, month, year):
    # Phụ cấp cố định: lấy tổng amount của tất cả loại cố định
    fixed_total = AllowanceType.objects.filter(is_fixed=True).aggregate(
        total=Sum("amount")
    )["total"] or 0

    # Phụ cấp linh hoạt: lấy từ các bản ghi EmployeeAllowance
    dynamic_total = EmployeeAllowance.objects.filter(
        employee=employee,
        date__month=month,
        date__year=year
    ).aggregate(total=Sum("amount"))["total"] or 0

    return round(fixed_total + dynamic_total, 2)
def calculate_actual_salary(employee, month, year, work_standard_days):
    # Lấy lương cơ bản
    base_salary = employee.base_salary.salary if employee.base_salary else 0
    salary_grade_coeff = employee.salary_grade.coefficient if employee.salary_grade else 1

    # Số ngày đi làm và hệ số công từ bảng timesheet
    timesheets = employee.timesheets.filter(month=month, year=year)
    working_days = timesheets.filter(work_coefficient__gt=0).count()
    total_coefficient = sum(t.work_coefficient for t in timesheets)

    # Thưởng - Phạt
    bonus, penalty = get_bonus_penalty(employee, month, year)

    # Tăng ca
    overtime_pay = get_total_overtime_pay(employee, month, year, work_standard_days)

    # Phụ cấp
    total_allowance = get_total_allowance(employee, month, year)


    # Tiền công 1 ngày
    daily_rate = (base_salary / work_standard_days) * salary_grade_coeff

    # Lương chính
    work_salary = daily_rate * total_coefficient

    # Tổng lương
    actual_salary = round(work_salary + bonus - penalty + overtime_pay + total_allowance)

    return {
        "working_days": working_days,
        "bonus": bonus,
        "penalty": penalty,
        "overtime_pay": overtime_pay,
        "allowance": total_allowance,
        "base_work_salary": work_salary,
        "actual_salary": actual_salary
    }


