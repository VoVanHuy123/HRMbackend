from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user.views import UserViewSet
routers = DefaultRouter()
routers.register('users', UserViewSet, basename='user')
urlpatterns = [
    path('', include(routers.urls)),

]