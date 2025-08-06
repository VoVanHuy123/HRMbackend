from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, generics,permissions,status

# model
from .models import (
    Timesheet,
    CommendationDiscipline,
    LeaveRequest,
    WorkType,
    Overtime,
    SalaryAdvance,
    AllowanceType,
)
from employee.models import (
    EmployeeAllowance
)
# serializers
from .serializers import *
# permissions
from user.permisions import IsAdminOrOwner,IsAdmin
# filters
from .filters import *
from django_filters.rest_framework import DjangoFilterBackend
# paginations
from .paginators import TimesheetPagination
# Create your views here.
class TimeSheetViewset(viewsets.ViewSet,generics.ListAPIView,generics.UpdateAPIView):
    queryset=Timesheet.objects.all()
    serializer_class = TimeSheetSerializers
    permission_classes = [IsAdminOrOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TimesheetFilter
    pagination_class = TimesheetPagination
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Timesheet.objects.none()
        user = self.request.user
        if hasattr(user, 'role') and user.role == "Admin":
            return Timesheet.objects.all()
        return Timesheet.objects.filter(employee=user.employee)
    def get_serializer_class(self):
        if self.action in ["update","partial_update"]:
            return UpdateTimeSheetSerializers
        return super().get_serializer_class()
    # def filter_queryset(self, queryset):
    #     user = self.request.user
    #     params = self.request.query_params

    #     if not hasattr(user, 'role') or user.role != "Admin":
    #         if 'employee_id' in params or 'name' in params:
    #             raise PermissionDenied("Bạn không có quyền lọc theo nhân viên.")
    #     return super().filter_queryset(queryset)
    def get_permissions(self):
        if(self.action in ["list","update","partial_update"]):
            return [IsAdminOrOwner()]
        return super().get_permissions()
    
    # @action(detail=True, methods=["get"], url_path="")
class CommendationDisciplineViewsets(viewsets.ViewSet, generics.CreateAPIView,generics.UpdateAPIView,generics.ListAPIView):
    queryset=CommendationDiscipline.objects.all()
    serializer_class = CommendationDisciplineSerializers
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CommendationDisciplineFilter
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())  # <- áp dụng filter từ query params
        commendations = queryset.filter(record_type='commendation')
        disciplines = queryset.filter(record_type='discipline')
        return Response({
            "commendations": CommendationDisciplineSerializers(commendations, many=True).data,
            "disciplines": CommendationDisciplineSerializers(disciplines, many=True).data
        })


    def get_serializer_class(self):
        if self.action in ["update","partial_update"]:
            return UpdateCommendationDisciplineSerializers
        return super().get_serializer_class()
    def get_permissions(self):
        if self.action in ['list']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

class LeaveRequestViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializers
    permission_classes=[permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LeaveRequestFilter

    def get_serializer_class(self):
        if self.action in ["create"]:
            return CreateLeaveRequestSerializers
        return super().get_serializer_class()
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return LeaveRequest.objects.none()
        user = self.request.user
        if hasattr(user, 'role') and user.role == "Admin":
            return LeaveRequest.objects.all()
        return LeaveRequest.objects.filter(employee=user.employee)
    def filter_queryset(self, queryset):
        user = self.request.user
        params = self.request.query_params

        if not hasattr(user, 'role') or user.role != "Admin":
            if 'employee_id' in params or 'name' in params:
                raise PermissionDenied("Bạn không có quyền lọc theo nhân viên.")
        return super().filter_queryset(queryset)
    def get_permissions(self):
        if(self.action == "list"):
            return [IsAdminOrOwner()]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        # Lấy user -> employee
        employee = request.user.employee  # Giả sử có OneToOneField giữa User và Employee
        data = request.data.copy()
        data['employee'] = employee.id  # Gán employee ID vào dữ liệu gửi đi

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WorkTypeViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = WorkType.objects.all()
    serializer_class = WorkTypeserializer
    permission_classes = [IsAdmin]
    def get_permissions(self):
        if(self.action=='list'):
            return [ permissions.IsAuthenticated()]
        return super().get_permissions()
class OverTimeViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView):
    queryset = Overtime.objects.all()
    serializer_class = OverTimeSerializers
    filter_backends = [DjangoFilterBackend]
    filterset_class = OverTimeFilter
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Overtime.objects.none()
        user = self.request.user
        if hasattr(user, 'role') and user.role == "Admin":
            return Overtime.objects.all()
        return Overtime.objects.filter(employee=user.employee)

    def get_serializer_class(self):
        if self.action in ["update","partial_update"]:
            return UpdateOverTimeSerializers
        if self.action in ["create"]:
            return createTimeSerializers
        return super().get_serializer_class()
    
class SalaryAdvanceViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = SalaryAdvance.objects.all()
    serializer_class = SalaryAdvanceSerializers
    filter_backends = [DjangoFilterBackend]
    filterset_class = SalaryAdvanceFilter

    def get_serializer_class(self):
        if self.action in ["update","partial_update"]:
            return UpdateSalaryAdvanceSerializers
        if self.action in ["create"]:
            return CreateSalaryAdvanceSerializers
        return super().get_serializer_class()
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SalaryAdvance.objects.none()
        user = self.request.user
        if hasattr(user, 'role') and user.role == "Admin":
            return SalaryAdvance.objects.all()
        return SalaryAdvance.objects.filter(employee=user.employee)
class AllowanceTypeViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.DestroyAPIView,generics.UpdateAPIView):
    queryset=AllowanceType.objects.all()
    serializer_class = AllowanceTypeSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AllowanceTypeFilter
    @action(
        detail=False,
        methods=["get"],
        url_path="not-fixed",  # Đổi url_path thành rõ nghĩa
        permission_classes=[permissions.IsAuthenticated]  # Bạn có thể sửa nếu cần
    )
    def get_allowance_type_not_fixed(self, request):
        queryset = AllowanceType.objects.filter(is_fixed=False)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

class EmployeeAllowanceViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.DestroyAPIView,generics.UpdateAPIView):
    queryset= EmployeeAllowance.objects.all()
    serializer_class = EmployeeAllowanceSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EmployeeAllowanceFilter
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return EmployeeAllowance.objects.none()
        user = self.request.user
        if hasattr(user, 'role') and user.role == "Admin":
            return EmployeeAllowance.objects.all()
        return EmployeeAllowance.objects.filter(employee=user.employee)
    def get_serializer_class(self):
        if self.action in ["update","partial_update"]:
            return UpdateEmployeeAllowanceSerializer
        if self.action in ["create"]:
            return CreateEmployeeAllowanceSerializer
        return super().get_serializer_class()
    def get_permissions(self):
        if self.action in ['list']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
class ShiftTypeViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset=ShiftType.objects.all()
    serializer_class = ShifTypeSerializer
    permission_classes = [IsAdmin]
    # filter_backends = [DjangoFilterBackend]
    # filterset_class = AllowanceTypeFilter
    def get_permissions(self):
        if(self.action == 'list'):
            return [permissions.IsAuthenticated()]
        return super().get_permissions()