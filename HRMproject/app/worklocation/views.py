
from django.shortcuts import render
import requests
from rest_framework import viewsets,generics,permissions
from app.user.permisions import IsAdmin,IsAdminOrOwner
from .models import WorkLocation
from .serializers import WorkLocationSerializer,CreateWorkLocationSerializer

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from services.loactions import haversine,get_work_location_by_employee_and_date

# Create your views here.
class WorklocationViewsets(viewsets.ViewSet,generics.ListCreateAPIView,generics.UpdateAPIView,generics.DestroyAPIView):
    queryset = WorkLocation.objects.all()
    serializer_class = WorkLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'role') and user.role == "Employee":
            WorkLocation.objects.filter(emplyee = user.employee)
        return super().get_queryset()
    

    def get_serializer_class(self):
        if self.action in ['create']:
            return CreateWorkLocationSerializer
        return super().get_serializer_class()
    def get_permissions(self):
        if self.action in ['update','partial_update','delete']:
            return [IsAdminOrOwner()]
        if self.action in ["search_address"]:
            return []
        return super().get_permissions()
    
    @action(detail=False, methods=["post"], url_path="check_location")
    def check_location(self, request, pk=None):
        user = request.user

        # Lấy employee từ user (nếu user có liên kết employee)
        employee = getattr(user, 'employee', None)
        if not employee:
            return Response({"error": "User chưa liên kết với nhân viên"}, status=status.HTTP_400_BAD_REQUEST)

        # Lấy vị trí làm việc theo nhân viên và ngày hiện tại
        work_location = get_work_location_by_employee_and_date(employee, timezone.now().date())
        if not work_location:
            return Response({"error": "Chưa đăng ký vị trí làm việc cho ngày hôm nay"}, status=status.HTTP_400_BAD_REQUEST)

        # Lấy dữ liệu latitude, longitude từ request
        try:
            user_lat = float(request.data.get('latitude'))
            user_lng = float(request.data.get('longitude'))
        except (TypeError, ValueError):
            return Response({"error": "Latitude và longitude không hợp lệ hoặc bị thiếu"}, status=status.HTTP_400_BAD_REQUEST)

        # Tính khoảng cách
        distance = haversine(user_lat, user_lng, float(work_location.latitude), float(work_location.longitude))

        # So sánh với radius cho phép (nếu bạn có trường này)
        # radius = getattr(work_location, 'radius', 1000)  # Mặc định 100 mét nếu không có
        radius = 1000

        if distance <= radius:
            return Response({"status": "OK", "distance": distance})
        else:
            return Response({"status": "FAIL", "distance": distance}, status=status.HTTP_403_FORBIDDEN)


    @action(detail=False, methods=["get"], url_path="search_address")
    def search_address(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response([], status=status.HTTP_200_OK)

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "format": "json",
            "q": q,
            "addressdetails": 1,
            "limit": 5,
            "accept-language": "vi",
            "countrycodes": "vn"  # Ưu tiên Việt Nam
        }
        headers = {
            "User-Agent": "HRMbackend/1.0 (admin@example.com)"  # bắt buộc
        }

        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            if r.status_code != 200:
                return Response(
                    {"error": f"Nominatim trả về lỗi {r.status_code}", "detail": r.text},
                    status=status.HTTP_502_BAD_GATEWAY
                )
            return Response(r.json(), status=status.HTTP_200_OK)

        except requests.exceptions.Timeout:
            return Response({"error": "Nominatim request timeout"}, status=status.HTTP_504_GATEWAY_TIMEOUT)

        except requests.RequestException as e:
            return Response({"error": "Cannot query Nominatim", "detail": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)