from django.shortcuts import render
from rest_framework import viewsets,generics
from .models import BaseSalary,SalaryGrade,WorkStandard
from user.permisions import IsAdmin
from .serializers import BaseSalarySerializer,SalaryGradeSerializer

# Create your views here.
class BaseSalaryViewset(viewsets.ViewSet,generics.ListAPIView):
    queryset = BaseSalary.objects.all()
    serializer_class = BaseSalarySerializer
    permission_classes = [IsAdmin]
class SalaryGradeViewset(viewsets.ViewSet,generics.ListAPIView):
    queryset = SalaryGrade.objects.all()
    serializer_class = SalaryGradeSerializer
    permission_classes = [IsAdmin]