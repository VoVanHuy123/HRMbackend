from django.contrib import admin

from .models import FaceEmbedding,FaceLog,FaceTrainingImage,FaceRecognitionFailure
# Register your models here.

admin.site.register(FaceTrainingImage)
admin.site.register(FaceEmbedding)
admin.site.register(FaceLog)
admin.site.register(FaceRecognitionFailure)