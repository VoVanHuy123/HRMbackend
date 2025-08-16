

from django.db.models import Sum, Count,Value,F
from datetime import date
from timesheet.models import Timesheet,Overtime
from django.db.models.functions import Concat
from employee.models import Employee, Department, Division


def round_float(value, digits=2):
    return round(value or 0, digits)

def get_employee_work_stats(employee_id, month=None, year=None):
    filters = {"employee_id": employee_id}
    if month:
        filters["month"] = month
    if year:
        filters["year"] = year

    timesheet_qs = Timesheet.objects.filter(**filters)
    total_hours = timesheet_qs.aggregate(
        total_hours=Sum("total_working_hours"),
        total_days=Count("id", distinct=True)
    )

    overtime_qs = Overtime.objects.filter(**filters)
    total_overtime_hours = overtime_qs.aggregate(
        total_hours=Sum("hours")
    )["total_hours"]

    worktype_stats = timesheet_qs.values(
        "work_type__id", "work_type__name"
    ).annotate(
        total_days=Count("id", distinct=True),
        total_hours=Sum("total_working_hours")
    )
    for wt in worktype_stats:
        wt["total_hours"] = round_float(wt["total_hours"])

    shifttype_stats = overtime_qs.values(
        "shift_type__id", "shift_type__name"
    ).annotate(
        total_days=Count("id", distinct=True),
        total_hours=Sum("hours")
    )
    for st in shifttype_stats:
        st["total_hours"] = round_float(st["total_hours"])

    return {
        "total_hours": round_float(total_hours["total_hours"]),
        "total_days": total_hours["total_days"] or 0,
        "total_overtime_hours": round_float(total_overtime_hours),
        "worktype_details": list(worktype_stats),
        "shifttype_details": list(shifttype_stats)
    }


def get_monthly_work_stats(employee_id, month, year=None):
    """
    Trả về tổng số giờ làm việc và số ngày làm việc trong tháng.
    """
    if year is None:
        year = date.today().year  # mặc định lấy năm hiện tại

    # Lọc timesheet theo tháng và năm
    queryset = Timesheet.objects.filter(
        employee_id=employee_id,
        month=month,
        year=year
    )

    # Tính tổng giờ làm việc và số ngày làm
    stats = queryset.aggregate(
        total_hours=Sum("total_working_hours"),
        work_days=Count("id")
    )

    return stats["total_hours"] or 0, stats["work_days"] or 0
def get_monthly_work_stats_all(month, year=None):
    """
    Tính tổng số giờ làm và tổng số ngày làm việc của tất cả nhân viên trong tháng.
    """
    if year is None:
        year = date.today().year  # Mặc định lấy năm hiện tại

    queryset = Timesheet.objects.filter(
        month=month,
        year=year
    )

    stats = queryset.aggregate(
        total_hours=Sum("total_working_hours")
    )

    return stats["total_hours"] or 0

def get_monthly_work_per_employee_in_division(division_id, month, year=None):
    """
    Lấy tổng số giờ làm việc của từng nhân viên trong một division theo tháng/năm.
    """
    if year is None:
        year = date.today().year

    queryset = (
        Timesheet.objects.filter(
            month=month,
            year=year,
            employee__division__id=division_id
        )
        .annotate(
            emp_id=F("employee_id"),
            name=Concat(
                F("employee__first_name"),
                Value(" "),
                F("employee__last_name")
            )
        )
        .values("emp_id", "name")
            .annotate(total_hours=Sum("total_working_hours"))
            .order_by("-total_hours")  # Sắp xếp giảm dần theo giờ
        )

    return list(queryset)


def get_office_statistics():
    stats = {
        "total_employees": Employee.objects.count(),
        "total_departments": Department.objects.count(),
        "total_divisions": Division.objects.count(),
        "departments": []
    }

    # Lấy danh sách phòng ban + các bộ phận bên trong
    departments = Department.objects.all()
    for dept in departments:
        divisions = (
            Division.objects
            .filter(department=dept)
            .annotate(employee_count=Count('employees', distinct=True))
            .values('id', 'name', 'employee_count')
        )

        stats["departments"].append({
            "id": dept.id,
            "name": dept.name,
            "division_count": divisions.count(),
            "employee_count": sum(d['employee_count'] for d in divisions),
        })

    return stats

