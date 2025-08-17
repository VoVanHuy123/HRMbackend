from django.shortcuts import render
from rest_framework import viewsets,generics,parsers
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate,get_user_model
from oauth2_provider.models import AccessToken, RefreshToken, Application
from oauthlib.common import generate_token
from django.utils.timezone import now
import datetime
from user.models import User
import dotenv
import sys
import os
from pathlib import Path
from rest_framework.response import Response
import requests
from user.serializers import UserSerializer,LoginSerializer,CreateUserSerializer, RefreshTokenSerializer
from rest_framework import status
import cloudinary.uploader
from django.core.management import call_command



# Đảm bảo .env được load
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(os.path.join(BASE_DIR, '.env'))
OAUTH_TOKEN_URL = "http://127.0.0.1:8000/o/token/"
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')



   
class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser,parsers.FormParser]

    def get_serializer_class(self):
        if self.action in ['create','update_user']:
            return CreateUserSerializer  # dùng serializer khác khi create
        return UserSerializer
    
    @swagger_auto_schema(
        method='post',
        request_body=LoginSerializer,
        responses={
            200: 'Access token and user info returned'
        },
        operation_description="Đăng nhập người dùng và lấy OAuth2 token."
    )
    @action(methods=['post'], detail=False, permission_classes=[])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"error": "Missing username or password"}, status=400)

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"error": "Sai tên đăng nhập hoặc mật khẩu"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            application = Application.objects.get(client_id=CLIENT_ID)
        except Application.DoesNotExist:
            return Response({"error": "OAuth2 Application not found"}, status=500)

        AccessToken.objects.filter(user=user, application=application).delete()
        RefreshToken.objects.filter(user=user, application=application).delete()

        access_token = AccessToken.objects.create(
            user=user,
            application=application,
            token=generate_token(),
            expires=now() + datetime.timedelta(seconds=3600),
            scope="read write"
        )

        refresh_token = RefreshToken.objects.create(
            user=user,
            application=application,
            token=generate_token(),
            access_token=access_token
        )
        return Response({
            "access_token": access_token.token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token.token,
            "user": UserSerializer(user).data
        })
    @action(detail=True, methods=["put"], url_path="update-user")
    def update_user(self, request, pk=None):
        user = self.get_object()
        data = request.data.copy()  # Dữ liệu để cập nhật

        # 1. Upload ảnh nếu có file avatar
        avatar_file = request.FILES.get('avatar')
        if avatar_file:
            result = cloudinary.uploader.upload(avatar_file)
            data['avatar'] = result.get("secure_url")

        # 2. Nếu password trống, loại bỏ để tránh set ''
        if data.get('password', '').strip() == '':
            data.pop('password', None)

        # 3. Gửi data vào serializer để validate & cập nhật
        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)

        # 4. Xử lý riêng password nếu có
        if 'password' in serializer.validated_data:
            user.set_password(serializer.validated_data.pop('password'))
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    from user.serializers import RefreshTokenSerializer

    @swagger_auto_schema(
        method='post',
        request_body=RefreshTokenSerializer,
        responses={200: 'New access token'},
        operation_description="Làm mới access token bằng refresh_token"
    )
    @action(methods=['post'], detail=False, permission_classes=[],url_path="refresh-token")
    def refresh_token(self, request):
        print("Request data:", request.data)
        refresh_token_str = request.data.get("refresh_token")
        if not refresh_token_str:
            return Response({"error": "Missing refresh_token"}, status=400)

        try:
            old_refresh = RefreshToken.objects.select_related("access_token", "user", "application").get(token=refresh_token_str)
        except RefreshToken.DoesNotExist:
            return Response({"error": "Invalid refresh_token"}, status=401)

        # Xoá token cũ
        old_refresh.access_token.delete()
        old_refresh.delete()

        user = old_refresh.user
        application = old_refresh.application

        # Tạo token mới
        access_token = AccessToken.objects.create(
            user=user,
            application=application,
            token=generate_token(),
            expires=now() + datetime.timedelta(seconds=3600),
            scope="read write"
        )

        refresh_token = RefreshToken.objects.create(
            user=user,
            application=application,
            token=generate_token(),
            access_token=access_token
        )

        return Response({
            "access_token": access_token.token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token.token
        })

    @action(methods=['post'], detail=False, url_path="initialize_system")
    def initialize_system(self, request):
        """
        API khởi tạo hệ thống:
        - Tạo/migrate tất cả bảng database
        - Tạo tài khoản admin mặc định
        """
        try:
            # 1. Kết nối database trước khi migrate
            from django.db import connection
            connection.ensure_connection()
            
            # 2. Migrate database
            from django.core.management import call_command
            call_command('makemigrations', interactive=False)
            call_command('migrate', interactive=False)
            
            # 3. Tạo superuser (cách an toàn hơn)
            User = get_user_model()
            if not User.objects.filter(username='admin').exists():
                admin = User.objects.create_user(
                    username='admin',
                    email='admin@example.com',
                    password='admin@123',
                    first_name='Admin',
                    last_name='System',
                    role='admin',
                    is_staff=True,
                    is_superuser=True
                )
                return Response({
                    'message': 'System initialized successfully',
                    'admin_created': True,
                    'admin_credentials': {
                        'username': 'admin',
                        'password': 'admin@123'  # Khuyến nghị dùng password mạnh
                    }
                }, status=status.HTTP_201_CREATED)
            return Response({
                'message': 'System already initialized',
                'admin_created': False
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            return Response({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)