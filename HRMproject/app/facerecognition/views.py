from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from cloudinary.uploader import upload
import numpy as np
import io
from PIL import Image
import base64
from services.face_reco import calculate_average_embedding

from .models import (
    FaceTrainingImage,
    FaceEmbedding
)
from employee.models import (
    Employee
)

class FaceRecognitionViewset(viewsets.ViewSet):
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
            defaults={"embedding": avg_embedding.tobytes()}
        )

        return Response({"message": "Đã huấn luyện và lưu embedding thành công"}, status=200)


