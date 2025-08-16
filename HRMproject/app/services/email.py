from django.core.mail import send_mail
from django.conf import settings

def send_payroll_email(employee, payroll):
    subject = f"Bảng lương tháng {payroll.month}/{payroll.year}"
    message = (
        f"Xin chào {employee.user.get_full_name()},\n\n"
        f"Bảng lương của bạn tháng {payroll.month}/{payroll.year} đã được tính:\n"
        f"- Ngày công: {payroll.working_day}\n"
        f"- Lương chính: {payroll.base_salary} VNĐ\n"
        f"- Tăng ca: {payroll.overtime_pay} VNĐ\n"
        f"- Thưởng: {payroll.bonus} VNĐ\n"
        f"- Phạt: {payroll.penalty} VNĐ\n"
        f"- Phụ cấp: {payroll.allowance} VNĐ\n"
        f"=> Thực lĩnh: {payroll.actual_salary} VNĐ\n\n"
        f"Trân trọng."
    )

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [employee.user.email])
