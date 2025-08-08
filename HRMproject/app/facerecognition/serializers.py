from rest_framework import serializers
from .models import FaceEmbedding
from employee.serializers import NameEmployeeSerializer
class FaceEmbeddingSerializer(serializers.ModelSerializer):
    employee = NameEmployeeSerializer()
    class Meta:
        model = FaceEmbedding
        
        fields = [
                  'employee',
                  "image",
                  "embedding",
                  ]