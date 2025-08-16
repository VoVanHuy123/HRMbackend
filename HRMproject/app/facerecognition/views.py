from django.shortcuts import render
from rest_framework import viewsets,generics,permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from cloudinary.uploader import upload
import numpy as np
from datetime import datetime, date
from django.utils import timezone
import io
from PIL import Image
import base64
from services.face_reco import calculate_average_embedding,extract_face_embedding,cosine_similarity

from user.permisions import IsAdmin

from .models import (
    FaceTrainingImage,
    FaceEmbedding,
    FaceRecognitionFailure,
    FaceLog,
    FaceTrackingSession
)
from employee.models import (
    Employee
)
from timesheet.models import (
    Timesheet,
    WorkType,
    ShiftType,
    Overtime
)
from .serializers import(
    FaceEmbeddingSerializer
)
from timesheet.serializers import (
    TimeSheetSerializers,
    OverTimeSerializers,
    TimeSheetEmployeeSerializers
)

class FaceRecognitionViewset(viewsets.ViewSet):
    permission_classes = [IsAdmin]
    def get_permissions(self):
        if(self.action in ["VerifyIdentity","OvertimeVerifyIdentity",'verify_face_tracking_sessions']):
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    @action(detail=False,methods=["post"], url_path="post_face_images")
    def PostFaceImage(self, request, *args, **kwargs):
        employee_id = request.data.get("employee_id")
        if not employee_id:
            return Response({"error": "Thiếu employee_id"}, status=400)

        employee = Employee.objects.filter(id=employee_id).first()
        if not employee:
            return Response({"error": "Không tìm thấy nhân viên"}, status=404)

        images = [f for k, f in request.FILES.items() if k.startswith("image_")]
        if len(images) < 3:
            return Response({"error": "Cần ít nhất 3 ảnh để train"}, status=400)

        embeddings = []

        for img_file in images:
            # Upload lên Cloudinary
            cloud_img = upload(img_file)
            url = cloud_img['secure_url']

            # Lưu vào FaceTrainingImage
            FaceTrainingImage.objects.create(employee=employee, image=url)
        return Response({"message": "Gửi ảnh thành công"}, status=200)
    
    @action(detail=False, methods=["post"], url_path="train_face_embedding")
    def TrainFaceEmbedding(self, request, *args, **kwargs):
        employee_id = request.data.get("employee_id")
        if not employee_id:
            return Response({"error": "Thiếu employee_id"}, status=400)

        employee = Employee.objects.filter(id=employee_id).first()
        if not employee:
            return Response({"error": "Không tìm thấy nhân viên"}, status=404)

        avg_embedding, error = calculate_average_embedding(employee)
        if error:
            return Response({"error": error}, status=400)

        FaceEmbedding.objects.update_or_create(
            employee=employee,
            defaults={
                "embedding": avg_embedding.astype(np.float32).tobytes()
            }
        )

        return Response({"message": "Đã huấn luyện và lưu embedding thành công"}, status=200)

    


    @action(detail=False, methods=["post"], url_path="verify_identity")
    def VerifyIdentity(self, request, *args, **kwargs):
        employee_id = request.data.get("employee_id")
        if not employee_id:
            return Response({"error": "Thiếu employee_id"}, status=400)

        employee = Employee.objects.filter(id=employee_id).first()
        if not employee:
            return Response({"error": "Không tìm thấy nhân viên"}, status=404)
        
        work_type_id = request.data.get("work_type_id")
        if not work_type_id:
            return Response({"error": "Thiếu work_type_id"}, status=400)
        work_type = WorkType.objects.filter(id=work_type_id).first()
        
        today = date.today()
        
        facelogs = FaceLog.objects.filter(
            employee=employee,
            timestamp__date=today,
            is_matched=True
        ).order_by("timestamp")  # để ảnh vào trước ra sau

        images = [log.image.url if log.image else None for log in facelogs]

        timesheet = Timesheet.objects.filter(employee=employee, date=today).first()
        if timesheet and timesheet.time_out:
                # Đã chấm công rồi => không cập nhật gì
                return Response({
                    "message": "Nhân viên đã chấm công xong hôm nay",
                    "employee_id": employee.id,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "timesheet": TimeSheetSerializers(timesheet).data,
                    "faceImages" : images
                })
        

        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "Thiếu ảnh"}, status=400)

        # Upload ảnh lên Cloudinary
        cloud_img = upload(image_file)
        image_url = cloud_img['secure_url']

        # Trích xuất embedding từ ảnh
        embedding = extract_face_embedding(image_url)
        if embedding is None:
            FaceRecognitionFailure.objects.create(
                image=image_file,
                reason="Không thể trích xuất embedding",
                note="Có thể do ảnh không có khuôn mặt rõ"
            )
            return Response({"error": "Không thể trích xuất embedding"}, status=400)

        # So sánh với embedding đã lưu
        all_embeddings = FaceEmbedding.objects.select_related("employee").all()
        if not all_embeddings:
            return Response({"error": "Không có dữ liệu embedding"}, status=404)

        best_match = None
        best_score = -1
        threshold = 0.7

        for fe in all_embeddings:
            db_embedding = np.frombuffer(fe.embedding, dtype=np.float32)
            if db_embedding.shape != embedding.shape:
                continue
            score = cosine_similarity(embedding, db_embedding)
            if score > best_score:
                best_score = score
                best_match = fe.employee

        if best_score >= threshold:
            # ✅ MATCHED — Ghi vào FaceLog
            if(employee.id == best_match.id):
                FaceLog.objects.create(
                    employee=best_match,
                    is_matched=True,
                    image=image_url,
                    confidence_score=round(float(best_score), 4),
                    note="Xác thực thành công"
                )


                # Cập nhật hoặc tạo timesheet
                now_time = datetime.now().time()
                if not timesheet:
                    timesheet=Timesheet.objects.create(employee=employee, date=today, time_in=now_time,work_type=work_type)
                else:
                    timesheet.time_out = now_time
                    timesheet.save()
                

                return Response({
                    "message": "Xác nhận thành công",
                    "employee_id": best_match.id,
                    "employee_name": f"{best_match.first_name} {best_match.last_name}",
                    "similarity": round(float(best_score), 4),
                    "timesheet": TimeSheetSerializers(timesheet).data,
                    "faceImages": [*images, image_url]
                })
            else:
                
                FaceLog.objects.create(
                    employee=employee,
                    is_matched=False,
                    image=image_url,
                    confidence_score=round(float(best_score), 4),
                    note=f"Xác thực thất bại (nhận diện thành nhân viên {employee.first_name} {employee.last_name})"
                )
                return Response({
                    "message": "Xác nhận thất bại",
                    # "employee_id": best_match.id,
                    # "employee_name": f"{best_match.first_name} {best_match.last_name}",
                    "similarity": round(float(best_score), 4),
                    "timesheet": TimeSheetSerializers(timesheet).data,
                    "faceImages": [*images, image_url]
                })
        else:
            # ❌ KHÔNG MATCH — Ghi vào FaceRecognitionFailure
            FaceRecognitionFailure.objects.create(
                image=image_file,
                reason="Không khớp với nhân viên nào",
                note=f"Độ tương đồng cao nhất: {round(float(best_score), 4)}"
            )
            return Response({"error": "Không xác định được danh tính"}, status=404)
        
    @action(detail=False, methods=["post"], url_path="overtime_verify_identity")
    def OvertimeVerifyIdentity(self, request, *args, **kwargs):
        employee_id = request.data.get("employee_id")
        if not employee_id:
            return Response({"error": "Thiếu employee_id"}, status=400)

        employee = Employee.objects.filter(id=employee_id).first()
        if not employee:
            return Response({"error": "Không tìm thấy nhân viên"}, status=404)
        
        shift_type_id = request.data.get("shift_type_id")
        if not shift_type_id:
            return Response({"error": "Thiếu shift_type_id"}, status=400)
        shift_type = ShiftType.objects.filter(id=shift_type_id).first()
        
        today = date.today()
        
        facelogs = FaceLog.objects.filter(
            employee=employee,
            timestamp__date=today,
            is_matched=True
        ).order_by("timestamp")  # để ảnh vào trước ra sau

        images = [log.image.url if log.image else None for log in facelogs]

        overtime = Overtime.objects.filter(employee=employee, date=today).first()
        if overtime and overtime.time_out:
                # Đã chấm công rồi => không cập nhật gì
                return Response({
                    "message": "Nhân viên đã chấm công xong hôm nay",
                    "employee_id": employee.id,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "overtime": OverTimeSerializers(overtime).data,
                    "faceImages" : images
                })
        

        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "Thiếu ảnh"}, status=400)

        # Upload ảnh lên Cloudinary
        cloud_img = upload(image_file)
        image_url = cloud_img['secure_url']

        # Trích xuất embedding từ ảnh
        embedding = extract_face_embedding(image_url)
        if embedding is None:
            FaceRecognitionFailure.objects.create(
                image=image_file,
                reason="Không thể trích xuất embedding",
                note="Có thể do ảnh không có khuôn mặt rõ"
            )
            return Response({"error": "Không thể trích xuất embedding"}, status=400)

        # So sánh với embedding đã lưu
        all_embeddings = FaceEmbedding.objects.select_related("employee").all()
        if not all_embeddings:
            return Response({"error": "Không có dữ liệu embedding"}, status=404)

        best_match = None
        best_score = -1
        threshold = 0.7

        for fe in all_embeddings:
            db_embedding = np.frombuffer(fe.embedding, dtype=np.float32)
            if db_embedding.shape != embedding.shape:
                continue
            score = cosine_similarity(embedding, db_embedding)
            if score > best_score:
                best_score = score
                best_match = fe.employee

        if best_score >= threshold:
            # ✅ MATCHED — Ghi vào FaceLog
            if(employee.id == best_match.id):
                FaceLog.objects.create(
                    employee=best_match,
                    is_matched=True,
                    image=image_url,
                    confidence_score=round(float(best_score), 4),
                    note="Xác thực thành công"
                )


                # Cập nhật hoặc tạo timesheet
                now_time = datetime.now().time()
                if not overtime:
                    overtime=Overtime.objects.create(employee=employee, date=today, time_in=now_time,shift_type=shift_type)
                else:
                    overtime.time_out = now_time
                    overtime.save()
                

                return Response({
                    "message": "Xác nhận thành công",
                    "employee_id": best_match.id,
                    "employee_name": f"{best_match.first_name} {best_match.last_name}",
                    "similarity": round(float(best_score), 4),
                    "overtime": OverTimeSerializers(overtime).data,
                    "faceImages": [*images, image_url]
                })
            else:
                
                FaceLog.objects.create(
                    employee=employee,
                    is_matched=False,
                    image=image_url,
                    confidence_score=round(float(best_score), 4),
                    note=f"Xác thực thất bại (nhận diện thành nhân viên {employee.first_name} {employee.last_name})"
                )
                return Response({
                    "message": "Xác nhận thất bại",
                    "employee_id": best_match.id,
                    "employee_name": f"{best_match.first_name} {best_match.last_name}",
                    "similarity": round(float(best_score), 4),
                    "overtime": OverTimeSerializers(overtime).data,
                    "faceImages": [*images, image_url]
                })
        else:
            # ❌ KHÔNG MATCH — Ghi vào FaceRecognitionFailure
            FaceRecognitionFailure.objects.create(
                image=image_file,
                reason="Không khớp với nhân viên nào",
                note=f"Độ tương đồng cao nhất: {round(float(best_score), 4)}"
            )
            return Response({"error": "Không xác định được danh tính"}, status=404)

    
    @action(detail=False, methods=["post"], url_path="verify_face_tracking_sessions")
    def verify_face_tracking_sessions(self, request, *args, **kwargs):
        today = timezone.localdate()
        employee_id = request.data.get("employee_id")

        if not employee_id:
            return Response({"error": "employee_id is required"}, status=400)
        employee = Employee.objects.filter(id=employee_id).first()
        if not employee:
            return Response({"error": "Không tìm thấy nhân viên"}, status=404)
        
        work_type_id = request.data.get("work_type_id")
        if not work_type_id:
            return Response({"error": "Thiếu work_type_id"}, status=400)
        work_type = WorkType.objects.filter(id=work_type_id).first()
        
        # Lấy timesheet của nhân viên trong ngày
        timesheet = Timesheet.objects.filter(
            employee=employee,
            date=today
        ).first()

        if not timesheet:
            return Response({"error": "Chưa bắt đầu công việc"}, status=404)
        elif not timesheet.time_out == None:
            return Response({ 
                "message": "Đã chấm công",
                "timesheet": TimeSheetEmployeeSerializers(timesheet).data,
            }, status=200)
        # Lấy tất cả sessions trong ngày
        sessions = FaceTrackingSession.objects.filter(
            employee=employee,
            start_time__date=today
        ).order_by("start_time")

        if not sessions.exists():
            return Response({"error": "No face tracking sessions found"}, status=404)

        total_seconds = 0
        for session in sessions:
            if session.end_time:
                total_seconds += (session.end_time - session.start_time).total_seconds()
            else:
                total_seconds += (timezone.now() - session.start_time).total_seconds()

        total_hours = round(total_seconds / 3600, 2)

        

        # Cập nhật dữ liệu timesheet
        last_session_end = sessions.last().end_time or timezone.now()
        timesheet.time_out = last_session_end.time()
        timesheet.total_working_hours = total_hours
        timesheet.work_type = work_type
        timesheet.save()

        return Response({
            "message": "Timesheet updated successfully",
            "timesheet": TimeSheetEmployeeSerializers(timesheet).data,
        })


class FaceEmbeddingViewset (viewsets.ViewSet,generics.ListAPIView):
    queryset = FaceEmbedding.objects.all()
    serializer_class = FaceEmbeddingSerializer
