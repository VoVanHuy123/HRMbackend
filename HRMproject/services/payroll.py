from app.timesheet.models import ( 
    Timesheet,
    
)
# def calculate_salary_for_employee(employee, month, year):
#     timesheets = Timesheet.objects.filter(employee=employee, month=month, year=year)
#     total_hours = sum([ts.total_working_hours for ts in timesheets])
#     overtime = sum([ts.overtime_hours for ts in timesheets if ts.overtime_hours])

#     base_salary = employee.salary
#     ot_salary = overtime * employee.overtime_rate

#     allowances = Allowance.objects.filter(employee=employee).aggregate(total=Sum('amount'))['total'] or 0
#     bonus = get_bonus(employee, month, year)
#     deductions = get_deductions(employee, month, year)

#     total = base_salary + ot_salary + allowances + bonus - deductions

#     Payroll.objects.update_or_create(
#         employee=employee, month=month, year=year,
#         defaults={
#             "total_working_hours": total_hours,
#             "base_salary": base_salary,
#             "overtime_salary": ot_salary,
#             "allowances": allowances,
#             "bonus": bonus,
#             "deductions": deductions,
#             "total_salary": total
#         }
#     )

from django.db.models import Sum

def get_bonus_penalty(employee, month, year):
    records = employee.commendations_disciplines.filter(
        date__month=month,
        date__year=year
    )
    bonus = records.filter(record_type='Commendation').aggregate(total=Sum('amount'))['total'] or 0
    penalty = records.filter(record_type='Discipline').aggregate(total=Sum('amount'))['total'] or 0
    return bonus, penalty
def get_total_overtime_pay(employee, month, year,work_standard_days):
    overtimes = employee.overtimes.filter(month=month, year=year)

    if not overtimes.exists():
        return 0

    base_salary = employee.base_salary.salary if employee.base_salary else 0
    # work_standard_days = WorkStandard.objects.first().standard_work_number or 26
    
    per_hour_rate = (base_salary / work_standard_days) / 7.5

    total = 0
    for ot in overtimes:
        if ot.shift_type:
            total += per_hour_rate * ot.hours * ot.shift_type.coefficient
        else:
            total += per_hour_rate * ot.hours

    return round(total, 2)
def calculate_actual_salary(employee, month, year,work_days):
    # Lấy lương cơ bản
    base_salary = employee.base_salary.salary if employee.base_salary else 0
    salary_grade_coeff = employee.salary_grade.coefficient if employee.salary_grade else 1

    # Công chuẩn
    # standard_work = WorkStandard.objects.first()
    # work_days = standard_work.standard_work_number if standard_work else 26

    # Số ngày đi làm và hệ số trung bình từ bảng timesheet
    timesheets = employee.timesheets.filter(month=month, year=year)
    working_days = timesheets.count()
    total_coefficient = sum(t.work_coefficient for t in timesheets)

    # Tiền thưởng - phạt
    bonus, penalty = get_bonus_penalty(employee, month, year)

    # Tăng ca
    overtime_pay = get_total_overtime_pay(employee, month, year)

    # Phụ cấp
    allowances = employee.employee_allowances.filter(date__month=month, date__year=year)
    total_allowance = allowances.aggregate(total=Sum('amount'))['total'] or 0

    # Tiền công 1 ngày
    daily_rate = (base_salary / work_days)

    # Lương chính
    work_salary = daily_rate * total_coefficient

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

