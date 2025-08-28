import numpy as np
import mediapipe as mp
# from services.face_reco import extract_face_embedding
from facerecognition.models import FaceTrainingImage
import face_recognition
from PIL import Image
import requests
from io import BytesIO
import cv2
import os
import io


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # trỏ đến HRMPROJECT/app
hat_path = os.path.join(BASE_DIR, "assets", "img", "hat.png")


def extract_face_embedding(image_or_url):
    try:
        if isinstance(image_or_url, str):
            print(" Đang tải ảnh từ URL:", image_or_url)
            response = requests.get(image_or_url)
            response.raise_for_status()

            # Mở bằng PIL, convert về RGB
            pil_image = Image.open(BytesIO(response.content)).convert("RGB")
            print(" Định dạng ảnh:", pil_image.mode)

            # Chuyển sang numpy array và ép kiểu uint8
            # sau khi convert về RGB
            image = np.array(pil_image).copy()

            # check shape
            print(" Kiểm tra shape:", image.shape, "dtype:", image.dtype)

            if image.dtype != np.uint8:
                print(" Force cast dtype")
                image = image.astype(np.uint8)

            if len(image.shape) == 2:
                print(" Ảnh gray, mở rộng thành RGB")
                image = np.stack([image]*3, axis=-1)
            elif image.shape[2] == 4:
                print(" Ảnh có alpha channel, bỏ alpha")
                image = image[:, :, :3]
        elif isinstance(image_or_url, Image.Image):
            print(" Chuyển đổi từ PIL Image sang numpy array")
            image = np.array(image_or_url.convert("RGB")).astype(np.uint8).copy()
        else:
            print(" Định dạng ảnh không hợp lệ")
            return None

        # Nhận diện khuôn mặt
        face_locations = face_recognition.face_locations(image, model="hog")
        print(" Số khuôn mặt tìm thấy:", len(face_locations))

        if not face_locations or len(face_locations) == 0:
            print(" Không tìm thấy khuôn mặt nào")
            return None

        encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
        if not encodings:
            print(" Không trích xuất được embedding")
            return None

        print(" Trích xuất thành công embedding")
        return encodings[0]

    except Exception as e:
        print(f" Lỗi extract_face_embedding: {e}")
        return None





def calculate_average_embedding(employee):
    training_images = FaceTrainingImage.objects.filter(employee=employee)
    if not training_images.exists():
        return None, "Chưa có ảnh huấn luyện"

    embeddings = []

    for image_obj in training_images:
        url = image_obj.image.url
        embedding = extract_face_embedding(url)
        if embedding is not None:
            embeddings.append(embedding)
        else:
            print(f"❌ Không nhận diện được khuôn mặt trong ảnh: {url}")

    if not embeddings:
        return None, "Không trích xuất được khuôn mặt nào"

    avg_embedding = np.mean(embeddings, axis=0)
    print(f"✅ Tính trung bình {len(embeddings)} ảnh cho nhân viên {employee}")
    return avg_embedding, None
def cosine_similarity(a, b):
    """
    Tính cosine similarity giữa hai vector numpy.
    Trả về giá trị trong khoảng [-1, 1]
    """
    a = np.array(a)
    b = np.array(b)
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)



hat_img = cv2.imread(hat_path, cv2.IMREAD_UNCHANGED)

def add_overlay_to_face(face_img, overlay_img=hat_img, scale=1.0, x_offset_extra=0, y_offset_extra=0, y_ratio=0.8):
    """
    face_img_bytes: bytes ảnh gốc
    overlay_img_path: đường dẫn ảnh PNG overlay (có alpha)
    scale: tỉ lệ thay đổi kích thước overlay
    x_offset_extra, y_offset_extra: offset thêm để điều chỉnh vị trí overlay
    y_ratio: vị trí vertical so với eye_center (0.8 cho mũ, 1.0 cho kính, v.v)
    
    Trả về: BytesIO ảnh PNG kết quả
    """
    overlay = cv2.imread(hat_path, cv2.IMREAD_UNCHANGED)
    print(overlay.shape, overlay.dtype)
    # # Decode bytes ảnh
    # nparr = np.frombuffer(face_img_bytes, np.uint8)
    # face_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    # Chuyển sang RGB cho face_recognition
    face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)

    # Detect landmarks
    face_landmarks_list = face_recognition.face_landmarks(face_img_rgb)
    if not face_landmarks_list:
        return None  # Không tìm thấy khuôn mặt

    landmarks = face_landmarks_list[0]
    left_eye = landmarks['left_eye']
    right_eye = landmarks['right_eye']

    # Tính trung tâm 2 mắt
    left_center = np.mean(left_eye, axis=0)
    right_center = np.mean(right_eye, axis=0)
    eye_center = ((left_center[0] + right_center[0]) / 2,
                  (left_center[1] + right_center[1]) / 2)
    eye_center = tuple(map(int, eye_center))

    print("Eye center:", eye_center, "Overlay size:", overlay.shape)
    # Đọc ảnh overlay
    overlay = overlay_img
    if overlay.shape[2] != 4:
        raise ValueError("Ảnh overlay phải có alpha channel (PNG)")

    # Resize overlay
    new_w = int(overlay.shape[1] * scale)
    new_h = int(overlay.shape[0] * scale)
    overlay = cv2.resize(overlay, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Tính vị trí overlay
    x_offset = int(eye_center[0] - new_w / 2 + x_offset_extra)
    y_offset = int(eye_center[1] - new_h * y_ratio + y_offset_extra)

    # Giới hạn biên ảnh
    x1, y1 = max(x_offset, 0), max(y_offset, 0)
    x2, y2 = min(x_offset + new_w, face_img.shape[1]), min(y_offset + new_h, face_img.shape[0])

    overlay_x1 = max(0, -x_offset)
    overlay_y1 = max(0, -y_offset)
    overlay_x2 = overlay_x1 + (x2 - x1)
    overlay_y2 = overlay_y1 + (y2 - y1)

    # Chèn overlay với alpha
    alpha_overlay = overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2, 3] / 255.0
    alpha_face = 1.0 - alpha_overlay

    for c in range(0, 3):
        face_img[y1:y2, x1:x2, c] = (alpha_overlay * overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2, c] +
                                     alpha_face * face_img[y1:y2, x1:x2, c])

    # Encode lại ảnh thành BytesIO
    _, buffer = cv2.imencode(".png", face_img)
    return io.BytesIO(buffer)
