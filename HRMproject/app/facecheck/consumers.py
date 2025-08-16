# # import time
# # import base64
# # from channels.generic.websocket import AsyncWebsocketConsumer

# # class FaceConsumer(AsyncWebsocketConsumer):
# #     async def connect(self):
# #         if self.scope["user"].is_anonymous:
# #             await self.close()
# #         else:
# #             self.last_frame = 0
# #             await self.accept()

# #     async def receive(self, text_data=None, bytes_data=None):
# #         now = time.time()

# #         # Giới hạn mỗi user gửi 1 frame / 5 giây
# #         if now - self.last_frame < 5:
# #             return
# #         self.last_frame = now

# #         # Giới hạn dung lượng (max 500KB)
# #         if text_data and len(text_data) > 500_000:
# #             return

# #         # Giải mã ảnh base64
# #         if text_data:
# #             img_data = base64.b64decode(text_data.split(",")[1])
# #             # TODO: xử lý nhận diện khuôn mặt bằng OpenCV/face_recognition
# #             await self.send_json({
# #                 "status": "ok",
# #                 "message": "Frame received & processed"
# #             })

# #     async def disconnect(self, code):
# #         pass


# # consumers.py
# import json
# import asyncio
# from channels.generic.websocket import AsyncWebsocketConsumer
# from django.core.files.base import ContentFile
# import base64
# from facerecognition.models import FaceLog, FaceEmbedding, FaceRecognitionFailure
# from employee.models import Employee
# import face_recognition
# import numpy as np
# from channels.db import database_sync_to_async
# from datetime import datetime
# from django.core.exceptions import ObjectDoesNotExist
# from asgiref.sync import sync_to_async

# class FaceTrackingConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.user = self.scope['user']
#         print(f"User attempting connection: {self.user}")

#         self.employee = await self.get_employee()
#         if self.user.is_anonymous or not self.employee:
#             await self.close()
#         else:
#             # Lấy subprotocol đầu tiên của client
#             chosen_protocol = None
#             if self.scope.get("subprotocols"):
#                 chosen_protocol = self.scope["subprotocols"][0]

#             await self.accept(subprotocol=chosen_protocol)
#             print(f"Employee {self.employee} connected for face tracking")

#     async def disconnect(self, close_code):
#         print(f"Employee {self.employee} disconnected")
#         pass

#     async def receive(self, text_data=None, bytes_data=None):
#         try:
#             data = json.loads(text_data)
#             frame_data = data.get('frame')
#             timestamp = data.get('timestamp')
            
#             # Xử lý frame ảnh
#             await self.process_frame(frame_data, timestamp)
            
#             # Gửi phản hồi
#             # await self.send(json.dumps({
#             #     'status': 'processed',
#             #     'timestamp': timestamp
#             # }))
            
#         except Exception as e:
#             await self.send(json.dumps({
#                 'status': 'error',
#                 'message': str(e)
#             }))
#             print(f"Error processing frame: {e}")

#     @database_sync_to_async
#     def get_employee(self):
#         """Lấy thông tin employee liên kết với user hiện tại"""
#         try:
#             # Kiểm tra xem user có thuộc tính employee không
#             if hasattr(self.user, 'employee'):
#                 return self.user.employee
#             return None
#         except ObjectDoesNotExist:
#             print(f"Employee not found for user {self.user}")
#             return None
#         except Exception as e:
#             print(f"Error getting employee: {e}")
#             return None

#     async def process_frame(self, frame_data, timestamp):
#         try:
#             print("vao đ")
#             # Giải mã ảnh từ base64
#             format, imgstr = frame_data.split(';base64,') 
#             ext = format.split('/')[-1]
#             image_data = base64.b64decode(imgstr)
            
#             # Nhận diện khuôn mặt
#             image = face_recognition.load_image_file(ContentFile(image_data))
#             face_locations = face_recognition.face_locations(image)
            
#             if not face_locations:
#                 await self.handle_recognition_failure(image_data, "No face detected")
#                 await self.send(json.dumps({
#                     'status': 'fail',
#                     'message': 'Không tìm thấy khuôn mặt',
#                     'timestamp': timestamp
#                 }))
#                 return
            
#             # Lấy embedding của nhân viên từ database
#             try:
#                 face_embedding =await sync_to_async(FaceEmbedding.objects.get)(employee=self.employee)
#                 known_embedding = np.frombuffer(face_embedding.embedding, dtype=np.float32)
#             except FaceEmbedding.DoesNotExist:
#                 await self.handle_recognition_failure(image_data, "No embedding found for employee")
#                 await self.send(json.dumps({
#                     'status': 'fail',
#                     'message': 'Chưa có dữ liệu huấn luyện cho nhân viên này',
#                     'timestamp': timestamp
#                 }))
#                 return
            
#             # So sánh khuôn mặt
#             current_embedding = face_recognition.face_encodings(image, known_face_locations=face_locations)[0]
#             matches = face_recognition.compare_faces([known_embedding], current_embedding)
#             face_distance = face_recognition.face_distance([known_embedding], current_embedding)
#             confidence = 1 - face_distance[0]
            
#             if(confidence > 0.6):
#                 await self.send(json.dumps({
#                     'status': 'success' if bool(matches[0]) else 'fail',
#                     'matched': bool(matches[0]),
#                     'confidence': float(confidence),
#                     'timestamp': timestamp,
#                     "employee_name":f"{self.employee.first_name} {self.employee.last_name}",
#                     "face_location": face_locations
#                 }))
#             else:
#                     await self.send(json.dumps({
#                     'status':  'fail',
#                     'matched': bool(matches[0]),
#                     'confidence': float(confidence),
#                     'timestamp': timestamp,
#                     "face_location": face_locations
#                 }))
            
#             print(f"Processed frame for {self.employee}: matched={matches[0]}, confidence={confidence}")
            
#         except Exception as e:
#             await self.handle_recognition_failure(image_data, str(e))
#             await self.send(json.dumps({
#                 'status': 'error',
#                 'message': str(e),
#                 'timestamp': timestamp
#             }))
#             raise e

#     async def handle_recognition_failure(self, image_data, reason):
#         # failure = FaceRecognitionFailure(
#         #     reason=reason,
#         # )
#         # failure.image.save(
#         #     f'failure_{datetime.now().timestamp()}.jpg',
#         #     ContentFile(image_data),
#         #     save=False  # để không save toàn bộ object ngay
#         # )
#         # await database_sync_to_async(failure.save)()
#         print(f"Recognition failed: {reason}")

import json
import time
import io
from PIL import Image
import numpy as np
import base64
import face_recognition
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from employee.models import Employee
from timesheet.models import Timesheet
from facerecognition.models import FaceEmbedding,FaceTrackingSession
from datetime import datetime

class FaceTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.employee = await self.get_employee()
        self.current_session_id = None
        self.current_timesheet_id = None
        self.last_frame = 0  # thời điểm xử lý frame cuối cùng

        if self.user.is_anonymous or not self.employee:
            await self.close()
        else:
            chosen_protocol = None
            if self.scope.get("subprotocols"):
                chosen_protocol = self.scope["subprotocols"][0]

            await self.accept(subprotocol=chosen_protocol)
            print(f"Employee {self.employee} connected for face tracking")

    async def disconnect(self, close_code):
        if self.current_session_id:
            await self.close_tracking_session()
        print(f"Employee {self.employee} disconnected, code={close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        # now = time.time()
        # if now - self.last_frame < 2:  # Giới hạn 2 giây mới xử lý 1 frame
        #     return
        # self.last_frame = now

        try:
            data = json.loads(text_data)
            frame_data = data.get('frame')
            timestamp = data.get('timestamp')
            
            await self.process_frame(frame_data, timestamp)

        except Exception as e:
            await self.send(json.dumps({
                'status': 'error',
                'message': str(e)
            }))
            print(f"Error processing frame: {e}")

    @database_sync_to_async
    def get_employee(self):
        try:
            if hasattr(self.user, 'employee'):
                return self.user.employee
            return None
        except ObjectDoesNotExist:
            return None

    async def process_frame(self, frame_data, timestamp):
        try:
            format, imgstr = frame_data.split(';base64,') 
            image_data = base64.b64decode(imgstr)

            # Đọc ảnh bằng Pillow + numpy
            image = np.array(Image.open(io.BytesIO(image_data)))

            face_locations = face_recognition.face_locations(image)
            if not face_locations:
                await self.send(json.dumps({
                    'status': 'fail',
                    'message': 'Không tìm thấy khuôn mặt',
                    'timestamp': timestamp
                }))
                return

            try:
                face_embedding = await sync_to_async(FaceEmbedding.objects.get)(employee=self.employee)
                known_embedding = np.frombuffer(face_embedding.embedding, dtype=np.float32)
            except FaceEmbedding.DoesNotExist:
                await self.send(json.dumps({
                    'status': 'fail',
                    'message': 'Chưa có dữ liệu huấn luyện cho nhân viên này',
                    'timestamp': timestamp
                }))
                return

            current_embedding = face_recognition.face_encodings(image, known_face_locations=face_locations)[0]
            matches = face_recognition.compare_faces([known_embedding], current_embedding)
            face_distance = face_recognition.face_distance([known_embedding], current_embedding)
            confidence = 1 - face_distance[0]

            if confidence > 0.6:
                await self.start_timesheet()
                await self.start_tracking_session() # tạo face_tracking_session 
                await self.send(json.dumps({
                    'status': 'success',
                    'matched': bool(matches[0]),
                    'confidence': float(confidence),
                    'timestamp': timestamp,
                    "employee_name": f"{self.employee.first_name} {self.employee.last_name}",
                    "face_location": face_locations
                }))
            else:
                await self.stop_tracking_session() # đóng face_tracking_session tồn tại
                await self.send(json.dumps({
                    'status': 'fail',
                    'matched': bool(matches[0]),
                    'confidence': float(confidence),
                    'timestamp': timestamp,
                    "face_location": face_locations
                }))

        except Exception as e:
            await self.send(json.dumps({
                'status': 'error',
                'message': str(e),
                'timestamp': timestamp
            }))
            raise e
    @sync_to_async
    def start_tracking_session(self):
        """Tạo session mới nếu chưa có."""
        if not self.current_session_id:
            session = FaceTrackingSession.objects.create(
                employee=self.employee,
                start_time=datetime.now(),
                end_time=None
            )
            self.current_session_id = session.id

    @sync_to_async
    def stop_tracking_session(self):
        """Đóng session nếu đang mở."""
        if self.current_session_id:
            session = FaceTrackingSession.objects.get(id=self.current_session_id)
            session.end_time = datetime.now()
            session.save()
            self.current_session_id = None

    @sync_to_async
    def close_tracking_session(self):
        """Kết thúc session khi disconnect."""
        if self.current_session_id:
            session = FaceTrackingSession.objects.get(id=self.current_session_id)
            session.end_time = datetime.now()
            session.save()
            self.current_session_id = None
    @sync_to_async
    def start_timesheet(self):
        # """tạo mới 1 timesheet."""
        # if not self.current_timesheet_id:
        #     timesheet = Timesheet.objects.create(
        #         employee=self.employee,
        #         time_in=datetime.now(),
        #         is_ordinary = False,
        #         note = "Công làm từ xa"
        #     )
        #     self.current_timesheet_id = timesheet.id
        """Tạo mới 1 timesheet nếu chưa tồn tại cho hôm nay."""
        today = datetime.now().date()
        
        # Tìm timesheet của nhân viên cho hôm nay
        timesheet = Timesheet.objects.filter(
            employee=self.employee,
            date=today
        ).first()

        if not timesheet:
            timesheet = Timesheet.objects.create(
                employee=self.employee,
                date=today,
                time_in=datetime.now(),
                is_ordinary=False,
                note="Công làm từ xa"
            )
        
        self.current_timesheet_id = timesheet.id
