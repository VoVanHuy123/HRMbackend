from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, generics,permissions,status
from services.stats import *

class StatsViewset(viewsets.ViewSet):
    @action(
        detail=False,
        methods=["get"],
        url_path="get_total_working_hours_by_employee",  # Đổi url_path thành rõ nghĩa
        permission_classes=[permissions.IsAuthenticated]  # Bạn có thể sửa nếu cần
    )
    def get_total_working_hours_by_employee(self, request):

        employee_id = request.query_params.get("employee_id")
        if not employee_id:
            return Response({"error":"Thiếu employee_id"})
        month = request.query_params.get("month")
        if not month:
            return Response({"error":"Thiếu month"})
        year = request.query_params.get("year")
        if not year:
            return Response({"error":"Thiếu year"})
        # period = request.data.get("period")
        # if not period:
        #     return Response({"error":"Thiếu period"})
        try:
            total_hours,work_days = get_monthly_work_stats(employee_id,month,year)

            data = {
                "working_hours": round(total_hours, 2),
                "work_days": round(work_days, 2),
            }

            return Response(data, status=200)

        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    @action(
        detail=False,
        methods=["get"],
        url_path="get_work_hours_all_employee",  # Đổi url_path thành rõ nghĩa
        permission_classes=[permissions.IsAuthenticated]  # Bạn có thể sửa nếu cần
    )
    def get_work_hours_all_employee(self, request):
        month = request.query_params.get("month")
        if not month:
            return Response({"error":"Thiếu month"})
        year = request.query_params.get("year")
        
        try:
            total_hours = get_monthly_work_stats_all(month,year)
            data = {
                "working_hours": round(total_hours, 2)
            }

            return Response(data,status=200)
            
        except ValueError as e:
            return Response({"error": str(e)},status=400)
        except Exception as e:
            return Response({"error": str(e)},status=500)
    @action(
        detail=False,
        methods=["get"],
        url_path="get_work_hours_per_employee_in_division",  # Đổi url_path thành rõ nghĩa
        permission_classes=[permissions.IsAuthenticated]  # Bạn có thể sửa nếu cần
    )
    def get_work_hours_per_employee_in_division(self, request):
        division_id = request.query_params.get("division_id")
        if not division_id:
            return Response({"error":"Thiếu division_id"})
        month = request.query_params.get("month")
        if not month:
            return Response({"error":"Thiếu month"})
        year = request.query_params.get("year")
        
        try:
            list = get_monthly_work_per_employee_in_division(division_id,month,year)
            data = {
                "employee_list": list
            }

            return Response(data, status=200)
            
        except ValueError as e:
            return Response({"error": str(e)},status=400)
        except Exception as e:
            return Response({"error": str(e)},status=500)
        
    @action(
        detail=False,
        methods=["get"],
        url_path="get_employee_stats",  # Đổi url_path thành rõ nghĩa
        permission_classes=[permissions.IsAuthenticated]  # Bạn có thể sửa nếu cần
    )
    def get_employee_stats(self, request):
        employee_id = request.query_params.get("employee_id")
        if not employee_id:
            return Response({"error":"Thiếu employee_id"})
        month = request.query_params.get("month")
        if not month:
            return Response({"error":"Thiếu month"})
        year = request.query_params.get("year")
        
        try:
            data = get_employee_work_stats(employee_id,month,year)
            

            return Response(data, status=200)
            
        except ValueError as e:
            return Response({"error": str(e)},status=400)
        except Exception as e:
            return Response({"error": str(e)},status=500)
    @action(
        detail=False,
        methods=["get"],
        url_path="get_office_stats",  # Đổi url_path thành rõ nghĩa
        permission_classes=[permissions.IsAuthenticated]  # Bạn có thể sửa nếu cần
    )
    def get_office_stats(self, request):
        # employee_id = request.query_params.get("employee_id")
        # if not employee_id:
        #     return Response({"error":"Thiếu employee_id"})
        # month = request.query_params.get("month")
        # if not month:
        #     return Response({"error":"Thiếu month"})
        # year = request.query_params.get("year")
        
        try:
            data = get_office_statistics()
            

            return Response(data, status=200)
            
        except ValueError as e:
            return Response({"error": str(e)},status=400)
        except Exception as e:
            return Response({"error": str(e)},status=500)
        