from django.shortcuts import render
from rest_framework import viewsets,generics,permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from cloudinary.uploader import upload
import numpy as np
import cv2
from datetime import datetime, date
from django.utils import timezone
import io
from io import BytesIO
from PIL import Image
import base64
from services.face_reco import (
    generate_augmented_faces,
    calculate_average_embedding,
    extract_face_embedding,
    cosine_similarity,
    add_overlay_to_face,
    extract_face_embedding_ArcFace,
    extract_face_embedding_ArcFace_2,
    find_best_match_vectorized,
    )
from threading import Thread
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
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # trỏ đến HRMPROJECT/app
hat_path = os.path.join(BASE_DIR, "assets", "img", "hat.png")
glass_path = os.path.join(BASE_DIR, "assets", "img", "glass.png")

class FaceRecognitionViewset(viewsets.ViewSet):
    permission_classes = [IsAdmin]
    def get_permissions(self):
        if(self.action in ["VerifyIdentity","OvertimeVerifyIdentity",'verify_face_tracking_sessions','VerifyIdentityTest']):
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
        if len(images) < 1:
            return Response({"error": "Cần ít nhất 3 ảnh để train"}, status=400)
        embeddings = []




        for img_file in images:

            # ---- Đọc file thành bytes ngay từ đầu ----
            file_bytes = img_file.read()
            np_bytes = np.frombuffer(file_bytes, np.uint8)

            # 1. Upload lên Cloudinary từ bytes
            bio1 = io.BytesIO(file_bytes)
            bio1.name = img_file.name
            cloud_img = upload(bio1, resource_type="image")
            url = cloud_img.get("secure_url")
            if not url:
                continue

            # 2. Extract embedding
            # embedding = extract_face_embedding(url)
            embedding = extract_face_embedding_ArcFace(url)
            if embedding is None:
                continue
            embeddings.append(embedding)
            FaceTrainingImage.objects.create(
                employee=employee,
                image=url,
                embedding=embedding.astype(np.float32).tobytes()
            )

            # 3. Decode sang numpy cho OpenCV
            img_np = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)
           
            glass_img = cv2.imread(glass_path, cv2.IMREAD_UNCHANGED)
            hat_img = cv2.imread(hat_path, cv2.IMREAD_UNCHANGED)
            overlay_list = [
                (glass_img, 0.4, 0, 90, 1.0),  # kính
                (hat_img, 0.8, 0, 15, 0.8)    # mũ
            ]

            augmented_images = generate_augmented_faces(img_np, overlay_imgs=overlay_list)

            for aug_img, desc in augmented_images:
                _, buf = cv2.imencode(".jpg", aug_img)
                bio = io.BytesIO(buf)
                bio.name = f"aug_{desc}.jpg"

                cloud_img = upload(bio, resource_type="image")
                url = cloud_img.get("secure_url")
                embedding = extract_face_embedding_ArcFace(url)
                if embedding is None:
                    continue
                embeddings.append(embedding)
                FaceTrainingImage.objects.create(
                    employee=employee,
                    image=url,
                    embedding=embedding.astype(np.float32).tobytes()
                )


          
        if not embeddings:
            return Response({"error": "Không lấy được embedding nào"}, status=400)

        # Tính trung bình embedding cho nhân viên
        avg_embedding = np.mean(embeddings, axis=0)


        FaceEmbedding.objects.update_or_create(
            employee=employee,
            defaults={"embedding": avg_embedding.astype(np.float32).tobytes()}
        )

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
        
        # facelogs = FaceLog.objects.filter(
        #     employee=employee,
        #     timestamp__date=today,
        #     is_matched=True
        # ).order_by("timestamp")  # để ảnh vào trước ra sau

        # images = [log.image.url if log.image else None for log in facelogs]

        timesheet = Timesheet.objects.filter(employee=employee, date=today).first()
        if timesheet and timesheet.time_out:
                # Đã chấm công rồi => không cập nhật gì
                return Response({
                    "message": "Nhân viên đã chấm công xong hôm nay",
                    "employee_id": employee.id,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "timesheet": TimeSheetSerializers(timesheet).data,
                    # "faceImages" : images
                })
        

        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "Thiếu ảnh"}, status=400)

        original_bytes = image_file.read()
        
        # 1️⃣ Dùng bản copy cho trích xuất embedding
        pil_img = Image.open(BytesIO(original_bytes))
        embedding = extract_face_embedding_ArcFace_2(pil_img)
        # embedding = extract_face_embedding(image_url)
        if embedding is None:
            FaceRecognitionFailure.objects.create(
                image=image_file,
                reason="Không thể trích xuất embedding",
                note="Có thể do ảnh không có khuôn mặt rõ"
            )
            return Response({"error": "Không thể trích xuất embedding"}, status=400)
        def upload_async(file_bytes,facelog_id):
            try:
                upload_file = BytesIO(file_bytes)
                upload_file.name = image_file.name  # giữ lại tên file để Cloudinary biết định dạng
                cloud_img = upload(upload_file)
                image_url = cloud_img['secure_url']
                # Sau khi upload xong có thể lưu vào DB (nếu cần)
                FaceLog.objects.filter(id=facelog_id).update(image=image_url)
                print(f"Ảnh đã upload: {image_url}")
            except Exception as e:
                print(f"Lỗi upload async: {e}")

        

        # So sánh với embedding đã lưu
        # all_embeddings = FaceEmbedding.objects.select_related("employee").all()
        all_embeddings = FaceTrainingImage.objects.select_related("employee").all()
        if not all_embeddings:
            return Response({"error": "Không có dữ liệu embedding"}, status=404)

        # Tạo danh sách embeddings và employees
        db_embeddings = []
        employees = []
        images = []

        for fe in all_embeddings:
            db_embedding = np.frombuffer(fe.embedding, dtype=np.float32)
            if db_embedding.shape == embedding.shape:  # chỉ lấy embedding cùng dimension
                db_embeddings.append(db_embedding)
                employees.append(fe.employee)
                images.append(str(fe.image))

        if not db_embeddings:
            return Response({"error": "Không có embedding nào trùng dimension"}, status=400)

        db_embeddings = np.array(db_embeddings)
        best_idx, best_score = find_best_match_vectorized(embedding, db_embeddings, employees)

        threshold = 0.7
        if best_score < threshold:
            return Response({"message": "Không tìm thấy ai phù hợp", "similarity": float(best_score)}, status=404)

        best_match = employees[best_idx]
        image_return = images[best_idx]
        
        if best_score >= threshold:
            # ✅ MATCHED — Ghi vào FaceLog
            if(employee.id == best_match.id):
                facelog = FaceLog.objects.create(
                    employee=best_match,
                    is_matched=True,
                    # image=image_url,
                    confidence_score=round(float(best_score), 4),
                    note="Xác thực thành công"
                )
                Thread(target=upload_async, args=(original_bytes,facelog.id)).start()

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
                    # "faceImages": [*images, image_url]
                })
            else:
                
                facelog  = FaceLog.objects.create(
                    employee=employee,
                    is_matched=False,
                    # image=image_url,
                    confidence_score=round(float(best_score), 4),
                    note=f"Xác thực thất bại (nhận diện thành nhân viên {employee.first_name} {employee.last_name})"
                )
                Thread(target=upload_async, args=(original_bytes,facelog.id)).start()
                return Response({
                    "message": "Xác nhận thất bại",
                    # "employee_id": best_match.id,
                    # "employee_name": f"{best_match.first_name} {best_match.last_name}",
                    "similarity": round(float(best_score), 4),
                    "timesheet": TimeSheetSerializers(timesheet).data,
                    # "faceImages": [*images, image_url]
                })
        else:
            # ❌ KHÔNG MATCH — Ghi vào FaceRecognitionFailure
            FaceRecognitionFailure.objects.create(
                # image=image_url,
                reason="Không khớp với nhân viên nào",
                note=f"Độ tương đồng cao nhất: {round(float(best_score), 4)}"
            )
            return Response({"error": "Không xác định được danh tính"}, status=404)


#  test api
    @action(detail=False, methods=["post"], url_path="verify_identity_test")
    def VerifyIdentityTest(self, request, *args, **kwargs):
        employee_id = request.data.get("employee_id")
        if not employee_id:
            return Response({"error": "Thiếu employee_id"}, status=400)

        employee = Employee.objects.filter(id=employee_id).first()
        if not employee:
            return Response({"error": "Không tìm thấy nhân viên"}, status=404)
        
        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "Thiếu ảnh"}, status=400)

        # Upload ảnh lên Cloudinary
        # cloud_img = upload(image_file)
        # image_url = cloud_img['secure_url']

        # Trích xuất embedding từ ảnh
        # embedding = extract_face_embedding_ArcFace(image_url)
        # Đọc dữ liệu gốc vào bộ nhớ
        original_bytes = image_file.read()
        
        # 1️⃣ Dùng bản copy cho trích xuất embedding
        pil_img = Image.open(BytesIO(original_bytes))
        # pil_img = Image.open(image_file)
        embedding = extract_face_embedding_ArcFace_2(pil_img)
        # embedding = extract_face_embedding(image_url)
        if embedding is None:
            FaceRecognitionFailure.objects.create(
                image=image_file,
                reason="Không thể trích xuất embedding",
                note="Có thể do ảnh không có khuôn mặt rõ"
            )
            return Response({"error": "Không thể trích xuất embedding"}, status=400)
        def upload_async(file_bytes):
            try:
                upload_file = BytesIO(file_bytes)
                upload_file.name = image_file.name  # giữ lại tên file để Cloudinary biết định dạng
                cloud_img = upload(upload_file)
                image_url = cloud_img['secure_url']

                # Sau khi upload xong có thể lưu vào DB (nếu cần)
                print(f"Ảnh đã upload: {image_url}")
            except Exception as e:
                print(f"Lỗi upload async: {e}")

        # Thread(target=upload_async, args=(original_bytes,)).start()

        # So sánh với embedding đã lưu
        # all_embeddings = FaceEmbedding.objects.select_related("employee").all()
        all_embeddings = FaceTrainingImage.objects.select_related("employee").all()
        if not all_embeddings:
            return Response({"error": "Không có dữ liệu embedding"}, status=404)


        # Tạo danh sách embeddings và employees
        db_embeddings = []
        employees = []
        images = []

        for fe in all_embeddings:
            db_embedding = np.frombuffer(fe.embedding, dtype=np.float32)
            if db_embedding.shape == embedding.shape:  # chỉ lấy embedding cùng dimension
                db_embeddings.append(db_embedding)
                employees.append(fe.employee)
                images.append(str(fe.image))

        if not db_embeddings:
            return Response({"error": "Không có embedding nào trùng dimension"}, status=400)

        db_embeddings = np.array(db_embeddings)
        best_idx, best_score = find_best_match_vectorized(embedding, db_embeddings, employees)

        threshold = 0.7
        if best_score < threshold:
            return Response({"message": "Không tìm thấy ai phù hợp", "similarity": float(best_score)}, status=404)

        best_match = employees[best_idx]
        image_return = images[best_idx]
            
        return Response({
                "message": "Xác nhận thành công",
                "employee_id": best_match.id,
                "employee_name": f"{best_match.first_name} {best_match.last_name}",
                "similarity": round(float(best_score), 4),
                # "image_send": image_url,
                "image_return":image_return
                # "timesheet": TimeSheetSerializers(timesheet).data,
                # "faceImages": [*images, image_url]
            })
        
        
    @action(detail=False, methods=["get"], url_path="test")
    def test_get_face_trainnig_embeding(self,request):
        embeddings = []
        all_embeddings = FaceTrainingImage.objects.select_related("employee").all()
        if not all_embeddings:
            return Response({"error": "Không có dữ liệu embedding"}, status=404)

        best_match = None
        best_score = -1
        threshold = 0.7
        embedding = extract_face_embedding("https://res.cloudinary.com/dnzjjdg0v/image/upload/v1755486225/eemgovs5wwhy5bwkd3am.jpg")
        print("embedding shape:", None if embedding is None else embedding.shape)

        for fe in all_embeddings:
            db_embedding = np.frombuffer(fe.embedding, dtype=np.float32)
            print("db shape:", db_embedding.shape)

            if embedding is None:
                print("❌ Không tạo được embedding từ ảnh test")
                continue

            if db_embedding.shape != embedding.shape:
                print("❌ Shape khác nhau, bỏ qua")
                continue

            score = cosine_similarity(embedding, db_embedding)
            embeddings.append(score)
            print("score: ",score)
            if score > best_score:
                best_score = score
                best_match = fe.employee


        return Response({"embeddings":embeddings},200)

        
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
        
        # facelogs = FaceLog.objects.filter(
        #     employee=employee,
        #     timestamp__date=today,
        #     is_matched=True
        # ).order_by("timestamp")  # để ảnh vào trước ra sau

        # images = [log.image.url if log.image else None for log in facelogs]

        overtime = Overtime.objects.filter(employee=employee, date=today).first()
        if overtime and overtime.time_out:
                # Đã chấm công rồi => không cập nhật gì
                return Response({
                    "message": "Nhân viên đã chấm công xong hôm nay",
                    "employee_id": employee.id,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "overtime": OverTimeSerializers(overtime).data,
                    # "faceImages" : images
                })
        

        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "Thiếu ảnh"}, status=400)

        original_bytes = image_file.read()
        
        # 1️⃣ Dùng bản copy cho trích xuất embedding
        pil_img = Image.open(BytesIO(original_bytes))
        embedding = extract_face_embedding_ArcFace_2(pil_img)
        # embedding = extract_face_embedding(image_url)
        if embedding is None:
            FaceRecognitionFailure.objects.create(
                image=image_file,
                reason="Không thể trích xuất embedding",
                note="Có thể do ảnh không có khuôn mặt rõ"
            )
            return Response({"error": "Không thể trích xuất embedding"}, status=400)
        def upload_async(file_bytes,facelog_id):
            try:
                upload_file = BytesIO(file_bytes)
                upload_file.name = image_file.name  # giữ lại tên file để Cloudinary biết định dạng
                cloud_img = upload(upload_file)
                image_url = cloud_img['secure_url']
                # Sau khi upload xong có thể lưu vào DB (nếu cần)
                FaceLog.objects.filter(id=facelog_id).update(image=image_url)
                print(f"Ảnh đã upload: {image_url}")
            except Exception as e:
                print(f"Lỗi upload async: {e}")

        

        # So sánh với embedding đã lưu
        # all_embeddings = FaceEmbedding.objects.select_related("employee").all()
        all_embeddings = FaceTrainingImage.objects.select_related("employee").all()
        if not all_embeddings:
            return Response({"error": "Không có dữ liệu embedding"}, status=404)

        # Tạo danh sách embeddings và employees
        db_embeddings = []
        employees = []
        images = []

        for fe in all_embeddings:
            db_embedding = np.frombuffer(fe.embedding, dtype=np.float32)
            if db_embedding.shape == embedding.shape:  # chỉ lấy embedding cùng dimension
                db_embeddings.append(db_embedding)
                employees.append(fe.employee)
                images.append(str(fe.image))

        if not db_embeddings:
            return Response({"error": "Không có embedding nào trùng dimension"}, status=400)

        db_embeddings = np.array(db_embeddings)
        best_idx, best_score = find_best_match_vectorized(embedding, db_embeddings, employees)

        threshold = 0.7
        if best_score < threshold:
            return Response({"message": "Không tìm thấy ai phù hợp", "similarity": float(best_score)}, status=404)

        best_match = employees[best_idx]
        image_return = images[best_idx]

        if best_score >= threshold:
            # ✅ MATCHED — Ghi vào FaceLog
            if(employee.id == best_match.id):
                FaceLog.objects.create(
                    employee=best_match,
                    is_matched=True,
                    # image=image_url,
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
                    # "faceImages": [*images, image_url]
                })
            else:
                
                FaceLog.objects.create(
                    employee=employee,
                    is_matched=False,
                    # image=image_url,
                    confidence_score=round(float(best_score), 4),
                    note=f"Xác thực thất bại (nhận diện thành nhân viên {employee.first_name} {employee.last_name})"
                )
                return Response({
                    "message": "Xác nhận thất bại",
                    "employee_id": best_match.id,
                    "employee_name": f"{best_match.first_name} {best_match.last_name}",
                    "similarity": round(float(best_score), 4),
                    "overtime": OverTimeSerializers(overtime).data,
                    # "faceImages": [*images, image_url]
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
