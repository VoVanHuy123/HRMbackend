from django.shortcuts import render
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from django.forms.models import model_to_dict
# import openpyxl
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status,permissions
from drf_yasg import openapi    
from rest_framework import viewsets,generics
from .models import (BaseSalary,
                     SalaryGrade,
                     WorkStandard,
                     Payroll,
                     PayrollHistory,
                     
)
from employee.models import Employee,EmployeeAllowance
from timesheet.models import AllowanceType
from user.permisions import IsAdmin,IsAdminOrOwner
from .serializers import *
from .filters import *
from django_filters.rest_framework import DjangoFilterBackend
from .paginators import PayRollPagination

from services.payroll import calculate_actual_salary
from datetime import datetime


# Create your views here.
class BaseSalaryViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = BaseSalary.objects.all()
    serializer_class = BaseSalarySerializer
    permission_classes = [IsAdmin]
class SalaryGradeViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = SalaryGrade.objects.all()
    serializer_class = SalaryGradeSerializer
    permission_classes = [IsAdmin]
    def get_permissions(self):
        if(self.action == 'list'):
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

class WorkStandardViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = WorkStandard.objects.all()
    serializer_class = WorkStandardSerializer
    permission_classes = [IsAdmin]
    def get_permissions(self):
        if(self.action=='list'):
            return [permissions.IsAuthenticated()]
        return super().get_permissions()


class PayrollViewset(viewsets.ViewSet, generics.ListAPIView, generics.UpdateAPIView, generics.CreateAPIView,generics.DestroyAPIView):
    queryset = Payroll.objects.all()
    serializer_class = PayRollSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PayrollFilter
    pagination_class = PayRollPagination

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return UpdatePayRollSerializer
        if self.action == "create":
            return CreatePayRollSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Payroll.objects.none()
        user = self.request.user
        if hasattr(user, 'role') and user.role == "Admin":
            return Payroll.objects.all()
        return Payroll.objects.filter(employee=user.employee)

    def get_permissions(self):
        if self.action == "list":
            return [IsAdminOrOwner()]
        return super().get_permissions()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_locked:
            return Response({"error": "Bảng lương đã khóa, không thể chỉnh sửa."}, status=400)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['month', 'year', 'standard_work_number_id'],
            properties={
                'month': openapi.Schema(type=openapi.TYPE_INTEGER),
                'year': openapi.Schema(type=openapi.TYPE_INTEGER),
                'standard_work_number_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'employee_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description="Optional: List of employee IDs to calculate salary for"
                ),
                'allowances': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'allowance_type_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'content': openapi.Schema(type=openapi.TYPE_STRING),
                            'date': openapi.Schema(type=openapi.TYPE_STRING, format="date"),
                        }
                    ),
                    description="Danh sách phụ cấp áp dụng cho mỗi nhân viên"
                )
            },
        ),
        responses={200: PayRollSerializer(many=True)},
        operation_description="Tính bảng lương cho toàn bộ hoặc nhóm nhân viên theo tháng, năm và công chuẩn"
    )
    @action(detail=False, methods=["post"], url_path="calculate", permission_classes=[IsAdmin])
    def calculate(self, request):
        data = request.data
        month = data.get("month")
        year = data.get("year")
        standard_id = data.get("standard_work_number_id")
        employee_ids = data.get("employee_ids", None)
        note = data.get("note", f"Bảng lương tháng {month}")

        if not all([month, year, standard_id]):
            return Response({"error": "Thiếu dữ liệu: month, year, standard_work_number_id"}, status=400)

        # Lấy công chuẩn
        try:
            work_standard = WorkStandard.objects.get(id=standard_id)
            standard_days = work_standard.standard_work_number
        except WorkStandard.DoesNotExist:
            return Response({"error": "Công chuẩn không tồn tại"}, status=404)

        # Lọc danh sách nhân viên
        employees = Employee.objects.filter(id__in=employee_ids) if employee_ids else Employee.objects.all()

        #Tạo allalow
        allowances = data.get("allowances", [])

        # validate trước nếu cần
        allowance_objs = []
        for al in allowances:
            try:
                al_type = AllowanceType.objects.get(id=al["allowance_type_id"])
                allowance_objs.append({
                    "type": al_type,
                    "amount": al["amount"],
                    "content": al.get("content", ""),
                    "date": datetime.strptime(al.get("date"), "%Y-%m-%d") if al.get("date") else None
                })
            except AllowanceType.DoesNotExist:
                return Response({"error": f"Phụ cấp loại ID {al['allowance_type_id']} không tồn tại"}, status=404)

        # vòng lặp mỗi nhân viên
        for emp in employees:
            # ... tính lương như cũ

        # 👉 tạo EmployeeAllowance cho nhân viên này nếu có phụ cấp
            for al in allowance_objs:
                EmployeeAllowance.objects.create(
                    employee=emp,
                    allowance_type=al["type"],
                    amount=al["amount"],
                    content=al["content"],
                    date=al["date"]
                )

        result = []

        for emp in employees:
            salary_data = calculate_actual_salary(emp, month, year, standard_days)

            # Lưu hoặc cập nhật bản ghi Payroll
            payroll, created = Payroll.objects.update_or_create(
                employee=emp,
                month=month,
                year=year,
                defaults={
                    "working_day": salary_data["working_days"],
                    "standard_work_number": standard_days,
                    "coefficient": emp.salary_grade.coefficient if emp.salary_grade else 1,
                    "base_salary": emp.base_salary.salary if emp.base_salary else 0,
                    "overtime_pay": salary_data["overtime_pay"],
                    "bonus": salary_data["bonus"],
                    "penalty": salary_data["penalty"],
                    "allowance": salary_data["allowance"],
                    "actual_salary": salary_data["actual_salary"],
                    "note": note,
                }
            )

            # So sánh dữ liệu cũ và mới
            tracked_fields = [
                "working_day", "coefficient", "base_salary",
                "overtime_pay", "bonus", "penalty",
                "allowance", "actual_salary"
            ]
            current_data = model_to_dict(payroll, fields=tracked_fields)
            # Nếu bản ghi mới hoặc có thay đổi thì lưu lịch sử
            last_history = PayrollHistory.objects.filter(payroll=payroll).last()
            if created or last_history is None or current_data != last_history.data:
                PayrollHistory.objects.create(
                    payroll=payroll,
                    updated_by=request.user.employee,
                    data=current_data,
                    note=note
                )

            result.append(payroll)

        serializer = PayRollSerializer(result, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='lock', permission_classes=[IsAdmin])
    def lock_payroll(self, request, pk=None):
        payroll = get_object_or_404(Payroll, pk=pk)
        if payroll.is_locked:
            return Response({"message": "Bảng lương đã bị khóa trước đó."}, status=200)
        payroll.is_locked = True
        payroll.save()
        return Response({"message": "Khóa bảng lương thành công."}, status=200)

    @action(detail=False, methods=["post"], url_path="lock-month", permission_classes=[IsAdmin])
    def lock_month(self, request):
        month = request.data.get("month")
        year = request.data.get("year")
        if not (month and year):
            return Response({"error": "Cần truyền tháng và năm."}, status=400)
        updated = Payroll.objects.filter(month=month, year=year).update(is_locked=True)
        return Response({"message": f"Đã khóa {updated} bảng lương tháng {month}/{year}."}, status=200)

    # @action(detail=False, methods=["get"], url_path="export-payroll-excel", permission_classes=[IsAdmin])
    # def export_payroll_excel(self, request):
    #     wb = openpyxl.Workbook()
    #     ws = wb.active
    #     ws.title = "Payroll"

    #     headers = ["Tên", "Tháng", "Năm", "Ngày công", "Lương cơ bản", "Thực lĩnh"]
    #     ws.append(headers)

    #     payrolls = self.get_queryset()
    #     for p in payrolls:
    #         ws.append([
    #             p.employee.user.get_full_name(),
    #             p.month,
    #             p.year,
    #             p.working_day,
    #             p.base_salary,
    #             p.actual_salary
    #         ])

    #     response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    #     response['Content-Disposition'] = 'attachment; filename=payroll.xlsx'
    #     wb.save(response)
    #     return response

    