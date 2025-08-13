from django.db import models
from HRMproject.models import BaseModel 
from cloudinary.models import CloudinaryField

# Create your models here.
class FaceEmbedding(BaseModel):
    employee = models.OneToOneField("employee.Employee", on_delete=models.CASCADE, primary_key=True, related_name='face_embedding', verbose_name="employee.Employee") # Assuming one embedding per employee
    # image_path = models.CharField(max_length=255, verbose_name="Image Path")
    image = CloudinaryField('image',null=True,blank=True)
    embedding = models.BinaryField(verbose_name="Embedding") # Storing the embedding as binary data (or JSONField if it's a list/array of floats)

    class Meta:
        verbose_name = "Face Embedding"
        verbose_name_plural = "Face Embeddings"
        db_table = "face_embedding"

    def __str__(self):
        return f"Embedding for {self.employee.first_name} {self.employee.last_name}"

class FaceLog(BaseModel):
    employee = models.ForeignKey("employee.Employee", on_delete=models.SET_NULL, null=True, blank=True, related_name='face_logs', verbose_name="employee.Employee") # Can be null if recognition fails
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    is_matched = models.BooleanField(verbose_name="Is Matched")
    # image_path = models.CharField(max_length=255, verbose_name="Image Path")
    image = CloudinaryField('image',null=True,blank=True)
    confidence_score = models.FloatField(null=True, blank=True, verbose_name="Confidence Score")
    note = models.TextField(blank=True, null=True, verbose_name="Note")
    

    class Meta:
        verbose_name = "Face Log"
        verbose_name_plural = "Face Logs"
        ordering = ['-timestamp'] # Order by latest log first
        db_table = "face_log"

    def __str__(self):
        employee_name = f"{self.employee.first_name} {self.employee.last_name}" if self.employee else 'Unknown'
        return f"Face log for {employee_name} at {self.timestamp}"
    
class FaceTrainingImage(models.Model):
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE, related_name="training_images")
    image = CloudinaryField('image',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Training image for {self.employee}"
class FaceRecognitionFailure(BaseModel):
    image = CloudinaryField('image',null=True,blank=True)  # ảnh không nhận diện được
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True, null=True)  # Ví dụ: "No face detected", "Low confidence"
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Face Recognition Failure"
        verbose_name_plural = "Face Recognition Failures"
        db_table = "face_recognition_failure"

    def __str__(self):
        return f"Failure at {self.timestamp} - {self.reason or 'Unknown'}"

class FaceTrackingSession(models.Model):
    employee = models.ForeignKey("employee.Employee", on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)  # Lúc ngừng nhận diện
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.start_time} -> {self.end_time or 'Đang hoạt động'}"