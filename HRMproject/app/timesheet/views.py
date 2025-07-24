from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, generics,permissions,status
from .models import Timesheet,CommendationDiscipline,LeaveRequest
from .serializers import TimeSheetSerializers,CommendationDisciplineSerializers,LeaveRequestSerializers
from user.permisions import IsAdminOrOwner,IsAdmin
from .filters import LeaveRequestFilter
from django_filters.rest_framework import DjangoFilterBackend
# Create your views here.
class TimeSheetViewset(viewsets.ViewSet):
    queryset=Timesheet.objects.all()
    serializer_class = TimeSheetSerializers
    permission_classes = [IsAdminOrOwner]

    # @action(detail=True, methods=["get"], url_path="")
class CommendationDisciplineViewsets(viewsets.ViewSet, generics.CreateAPIView):
    queryset=CommendationDiscipline.objects.all()
    serializer_class = CommendationDisciplineSerializers
    permission_classes = [IsAdmin]

class LeaveRequestViewset(viewsets.ViewSet,generics.ListCreateAPIView):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializers
    permission_classes=[permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LeaveRequestFilter

    def get_queryset(self):
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



