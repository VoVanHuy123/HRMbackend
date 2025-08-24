from django.shortcuts import render
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi    
from rest_framework import viewsets,generics,parsers,permissions,status
from rest_framework.response import Response
from .models import Employee,Contract,Department,Division,Qualification,Position,Insurance
from timesheet.models import Timesheet,CommendationDiscipline
from timesheet.serializers import TimeSheetSerializers,CommendationDisciplineSerializers
from .serializers import *
from .paginators import EmployeePaginator
from user.permisions import IsAdmin,IsAdminOrOwner
from django_filters.rest_framework import DjangoFilterBackend
import cloudinary
from .filters import EmployeeFilter
from datetime import datetime
# Create your views here.

class EmployeeViewset(viewsets.ViewSet,generics.RetrieveAPIView,generics.CreateAPIView,generics.ListAPIView,generics.DestroyAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    pagination_class = EmployeePaginator
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EmployeeFilter
    def get_permissions(self):
        if self.action in ["create","list","destroy","update"]:
            return [IsAdmin()] 
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'list':
            return ListEmployeeSerializer  
        if self.action == 'partial_update':
            return UpdateEmployeeSerializer  
        if self.action == 'office_info_update':
            return OfficeEmployeeSerializer  
        return EmployeeSerializer
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()  # Ensure it's mutable

        # Các trường cần cập nhật
        update_fields = [
            'first_name', 'last_name', 'gender', 'date_of_birth',
            'phone_number', 'citizen_id', 'address', 'email',"active",
        ]

        for field in update_fields:
            if field in data:
                setattr(instance, field, data[field])
        if 'photo' in data and data['photo']:
            uploaded = cloudinary.uploader.upload(data['photo'])
            instance.photo = uploaded.get("secure_url")
            print("vào")

        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @action(detail=True, methods=["patch"], url_path="office_info_update", permission_classes=[IsAdmin])
    def office_info_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    @swagger_auto_schema(
        method='get',
        # request_body=LoginSerializer,
            responses={200: openapi.Response(
            description="Danh sách bộ phận (Division) của phòng ban",
            schema=TimeSheetSerializers(many=True),)},
        # operation_description="Đăng nhập người dùng và lấy OAuth2 token."
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="timesheets",
        permission_classes=[IsAdminOrOwner]
    )
    def get_employee_timesheets(self, request, pk=None):
        # Lấy employee theo pk
        try:
            employee = Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return Response({"error": "Không tìm thấy Employee"}, status=status.HTTP_404_NOT_FOUND)

        # Lấy tháng và năm từ query params, ví dụ ?month=7&year=2025
        month = request.query_params.get("month")
        year = request.query_params.get("year")

        if not month or not year:
            # timesheets = Timesheet.objects.filter(
            # employee=employee,)
            # serializer = TimeSheetSerializers(timesheets, many=True)
            # return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"error": "không có tháng và năm ."}, status=status.HTTP_400_BAD_REQUEST)
        self.check_object_permissions(request, employee)
        try:
            month = int(month)
            year = int(year)
        except ValueError:
            return Response({"error": "Month and year must be integers."}, status=status.HTTP_400_BAD_REQUEST)

        # Lọc bảng công theo tháng
        timesheets = Timesheet.objects.filter(
            employee=employee,
            year=year,
            month=month
        )

        serializer = TimeSheetSerializers(timesheets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='get',
        # request_body=LoginSerializer,
            responses={200: openapi.Response(
            description="Danh sách Khen thưởng và kỷ luật",
            schema=CommendationDisciplineSerializers(many=True),)},
        # operation_description="Đăng nhập người dùng và lấy OAuth2 token."
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="commendations_disciplines",
        permission_classes=[IsAdminOrOwner]
    )
    def get_commendations_disciplines(self, request, pk=None):
        queryset = CommendationDiscipline.objects.filter(employee__id=pk)

        # Lọc theo ngày, tháng, năm nếu có
        date_str = request.GET.get('date')
        month = request.GET.get('month')
        year = request.GET.get('year')

        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(date=date_obj)
            except ValueError:
                return Response({'error': 'Invalid date format, must be YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        if month:
            queryset = queryset.filter(date__month=month)

        if year:
            queryset = queryset.filter(date__year=year)

        commendations = queryset.filter(record_type='commendation')
        disciplines = queryset.filter(record_type='discipline')

        return Response({
            "commendations": CommendationDisciplineSerializers(commendations, many=True).data,
            "disciplines": CommendationDisciplineSerializers(disciplines, many=True).data
        })

class ContractViewset(viewsets.ViewSet, generics.RetrieveAPIView, generics.CreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = Contract.objects.filter(active = True)
    serializer_class = ContractSerializer
    permission_classes = [IsAdmin]
class DepartmentViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_permissions(self):
        if self.action == "create":
            return [IsAdmin()]
        return super().get_permissions()
    
    @swagger_auto_schema(
        method='get',
        # request_body=LoginSerializer,
        responses={200: openapi.Response(
            description="Danh sách bộ phận (Division) của phòng ban",
            schema=DivisionSerializer(many=True),)},
        # operation_description="Đăng nhập người dùng và lấy OAuth2 token."
    )

    @action(detail=True, methods=["get"], url_path="divisions")
    def get_department_divisions(self, request, pk=None):
        # Lấy tất cả Division thuộc Department có id = pk
        divisions = Division.objects.filter(department_id=pk)
        serializer = DivisionSerializer(divisions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DivisionViewset(viewsets.ViewSet,generics.CreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = Division.objects.all()
    serializer_class = DivisionSerializer
    permission_classes = [IsAdmin]
    # def get_permissions(self):
    #     if self.action == "create":
    #         return [IsAdmin()]
    #     return super().get_permissions()
class QualificationViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = Qualification.objects.all()
    serializer_class = QualificationSerializer
    permission_classes = [IsAdmin]
    def get_permissions(self):
        if self.action == "list":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
class PositionViewset(viewsets.ViewSet,generics.ListCreateAPIView,generics.CreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsAdmin]

    def get_permissions(self):
        if self.action == "list":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

class InsuranceViewset(viewsets.ViewSet,generics.CreateAPIView,generics.RetrieveUpdateDestroyAPIView):
    queryset = Insurance.objects.all()
    serializer_class = InsuranceSerializer
    permission_classes = [IsAdmin]

    def get_serializer_class(self, *args, **kwargs):
        if(self.action in ["create","update"]):
            return CreateInsuranceSerializer
        return super().get_serializer_class(*args, **kwargs)

    def get_permissions(self):
        if self.action == "retrieve":
            return [IsAdminOrOwner()]
        return super().get_permissions()
