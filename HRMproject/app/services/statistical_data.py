from django.db.models import Count, Q

def get_working_days(employee, month, year):
    return employee.timesheets.filter(
        month=month,
        year=year,
        total_working_hours__gt=0
    ).count()
