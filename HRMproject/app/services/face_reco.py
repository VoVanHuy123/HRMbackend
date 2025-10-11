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
import random


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



import insightface


model = insightface.app.FaceAnalysis(name="buffalo_l")  # "buffalo_l" = model chuẩn, cân bằng tốc độ/độ chính xác
model.prepare(ctx_id=-1)  # ctx_id=-1 = chạy CPU, nếu có GPU thì dùng ctx_id=0

def extract_face_embedding_ArcFace(image_or_path):
    try:
        if isinstance(image_or_path, str):
            response = requests.get(image_or_path)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content)).convert("RGB")
        elif isinstance(image_or_path, Image.Image):
            img = image_or_path.convert("RGB")
        else:
            print("❌ Định dạng ảnh không hợp lệ")
            return None

        img = np.array(img)
        faces = model.get(img)

        if len(faces) == 0:
            print("❌ Không tìm thấy khuôn mặt")
            return None

        # InsightFace cho embedding 512 chiều
        embedding = faces[0].embedding
        return embedding

    except Exception as e:
        print(f"❌ Lỗi extract_face_embedding: {e}")
        return None


def extract_face_embedding_ArcFace_2(image_or_path):
    try:
        if isinstance(image_or_path, str):  # URL
            response = requests.get(image_or_path)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGB")
        elif isinstance(image_or_path, Image.Image):  # PIL Image
            img = image_or_path.convert("RGB")
        else:
            print("❌ Định dạng ảnh không hợp lệ")
            return None

        img = np.array(img)
        faces = model.get(img)

        if len(faces) == 0:
            print("❌ Không tìm thấy khuôn mặt")
            return None

        return faces[0].embedding  # 512-d embedding
    except Exception as e:
        print(f"❌ Lỗi extract_face_embedding: {e}")
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


glass_path = os.path.join(BASE_DIR, "assets", "img", "glass.png")
hat_img = cv2.imread(hat_path, cv2.IMREAD_UNCHANGED)
glass_img = cv2.imread(glass_path, cv2.IMREAD_UNCHANGED)

# def add_overlay_to_face(face_img, overlay_img=glass_img, scale=1.0, x_offset_extra=0, y_offset_extra=0, y_ratio=0.8):
#     """
#     face_img_bytes: bytes ảnh gốc
#     overlay_img_path: đường dẫn ảnh PNG overlay (có alpha)
#     scale: tỉ lệ thay đổi kích thước overlay
#     x_offset_extra, y_offset_extra: offset thêm để điều chỉnh vị trí overlay
#     y_ratio: vị trí vertical so với eye_center (0.8 cho mũ, 1.0 cho kính, v.v)
    
#     """
#     overlay = cv2.imread(hat_path, cv2.IMREAD_UNCHANGED)
#     print(overlay.shape, overlay.dtype)
#     # # Decode bytes ảnh
#     # nparr = np.frombuffer(face_img_bytes, np.uint8)
#     # face_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
#     # Chuyển sang RGB cho face_recognition
#     face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)

#     # Detect landmarks
#     face_landmarks_list = face_recognition.face_landmarks(face_img_rgb)
#     if not face_landmarks_list:
#         return None  # Không tìm thấy khuôn mặt

#     landmarks = face_landmarks_list[0]
#     left_eye = landmarks['left_eye']
#     right_eye = landmarks['right_eye']

#     # Tính trung tâm 2 mắt
#     left_center = np.mean(left_eye, axis=0)
#     right_center = np.mean(right_eye, axis=0)
#     eye_center = ((left_center[0] + right_center[0]) / 2,
#                   (left_center[1] + right_center[1]) / 2)
#     eye_center = tuple(map(int, eye_center))

#     print("Eye center:", eye_center, "Overlay size:", overlay.shape)
#     # Đọc ảnh overlay
#     overlay = overlay_img
#     if overlay.shape[2] != 4:
#         raise ValueError("Ảnh overlay phải có alpha channel (PNG)")

#     # Resize overlay
#     new_w = int(overlay.shape[1] * scale)
#     new_h = int(overlay.shape[0] * scale)
#     overlay = cv2.resize(overlay, (new_w, new_h), interpolation=cv2.INTER_AREA)

#     # Tính vị trí overlay
#     x_offset = int(eye_center[0] - new_w / 2 + x_offset_extra)
#     y_offset = int(eye_center[1] - new_h * y_ratio + y_offset_extra)

#     # Giới hạn biên ảnh
#     x1, y1 = max(x_offset, 0), max(y_offset, 0)
#     x2, y2 = min(x_offset + new_w, face_img.shape[1]), min(y_offset + new_h, face_img.shape[0])

#     overlay_x1 = max(0, -x_offset)
#     overlay_y1 = max(0, -y_offset)
#     overlay_x2 = overlay_x1 + (x2 - x1)
#     overlay_y2 = overlay_y1 + (y2 - y1)

#     # Chèn overlay với alpha
#     alpha_overlay = overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2, 3] / 255.0
#     alpha_face = 1.0 - alpha_overlay

#     for c in range(0, 3):
#         face_img[y1:y2, x1:x2, c] = (alpha_overlay * overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2, c] +
#                                      alpha_face * face_img[y1:y2, x1:x2, c])

#     # Encode lại ảnh thành BytesIO
#     _, buffer = cv2.imencode(".png", face_img)
#     return io.BytesIO(buffer)




# def augment_face_image(img_np, rotate_angles=[-15, 0, 15], brightness_range=(0.7, 1.3), contrast_range=(0.7, 1.3)):
#     """
#     img_np: numpy array ảnh gốc (BGR)
#     rotate_angles: list góc xoay (độ) để mô phỏng góc chụp khác
#     brightness_range: khoảng điều chỉnh độ sáng (nhân hệ số)
#     contrast_range: khoảng điều chỉnh độ tương phản (nhân hệ số)
    
#     return: list các ảnh augment (numpy array)
#     """
#     results = []

#     # 1. Ảnh gốc trắng đen
#     gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
#     gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
#     results.append(gray_bgr)

#     # 2. Điều chỉnh độ sáng / tương phản (random trong khoảng)
#     alpha = random.uniform(*contrast_range)  # contrast
#     beta = random.uniform(*brightness_range) * 50 - 25  # brightness shift (-25 đến +25)
#     bright_contrast = cv2.convertScaleAbs(img_np, alpha=alpha, beta=beta)
#     results.append(bright_contrast)

#     # 3. Xoay ảnh mô phỏng góc khác
#     h, w = img_np.shape[:2]
#     for angle in rotate_angles:
#         M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
#         rotated = cv2.warpAffine(img_np, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
#         results.append(rotated)

#     return results

def generate_augmented_faces(
    face_img,
    overlay_imgs=None,   # list các ảnh overlay (kính, mũ, khẩu trang...)
    rotate_angles=[-15, 0, 15],
    brightness_range=(50, 80),
    contrast_range=(0.7, 1.3)
):
    """
    Pipeline xử lý ảnh khuôn mặt:
    - Trắng đen
    - Điều chỉnh sáng / tương phản
    - Xoay góc
    - Thêm overlay (kính, mũ...)

    face_img: numpy array BGR ảnh gốc
    overlay_imgs: list tuple [(overlay_img, scale, x_offset, y_offset, y_ratio), ...]

    return: list tuple [(augmented_img, desc), ...]
    """
    results = []

    # 1️⃣ Ảnh gốc trắng đen
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    results.append((gray_bgr, "gray"))

    # 2️⃣ Điều chỉnh sáng / tương phản
    alpha = random.uniform(*contrast_range)  # contrast
    beta = random.uniform(*brightness_range) # brightness shift
    bright_contrast = cv2.convertScaleAbs(face_img, alpha=alpha, beta=beta)
    results.append((bright_contrast, f"bright_contrast_{alpha:.2f}_{beta:.2f}"))

    # 3️⃣ Xoay ảnh mô phỏng góc khác
    h, w = face_img.shape[:2]
    for angle in rotate_angles:
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        rotated = cv2.warpAffine(face_img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        results.append((rotated, f"rotated_{angle}"))

    # 4️⃣ Thêm overlay (kính, mũ...)
    if overlay_imgs:
        for overlay_img, scale, x_off, y_off, y_ratio in overlay_imgs:
            overlayed = add_overlay_to_face(face_img.copy(), overlay_img, scale, x_off, y_off, y_ratio)
            if overlayed is not None:
                results.append((overlayed, "overlay"))

    return results

def add_overlay_to_face(face_img, overlay_img, scale=1.0, x_offset_extra=0, y_offset_extra=0, y_ratio=0.8):
    """
    Chèn overlay (PNG có alpha) lên mặt tại vị trí dựa theo mắt.
    """
    face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    face_landmarks_list = face_recognition.face_landmarks(face_img_rgb)
    if not face_landmarks_list:
        return None  # Không tìm thấy khuôn mặt

    landmarks = face_landmarks_list[0]
    left_eye = landmarks['left_eye']
    right_eye = landmarks['right_eye']

    # Trung tâm 2 mắt
    left_center = np.mean(left_eye, axis=0)
    right_center = np.mean(right_eye, axis=0)
    eye_center = ((left_center[0] + right_center[0]) / 2,
                  (left_center[1] + right_center[1]) / 2)
    eye_center = tuple(map(int, eye_center))

    if overlay_img.shape[2] != 4:
        raise ValueError("Overlay phải là PNG có alpha channel")

    # Resize overlay
    new_w = int(overlay_img.shape[1] * scale)
    new_h = int(overlay_img.shape[0] * scale)
    overlay = cv2.resize(overlay_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    x_offset = int(eye_center[0] - new_w / 2 + x_offset_extra)
    y_offset = int(eye_center[1] - new_h * y_ratio + y_offset_extra)

    x1, y1 = max(x_offset, 0), max(y_offset, 0)
    x2, y2 = min(x_offset + new_w, face_img.shape[1]), min(y_offset + new_h, face_img.shape[0])

    overlay_x1 = max(0, -x_offset)
    overlay_y1 = max(0, -y_offset)
    overlay_x2 = overlay_x1 + (x2 - x1)
    overlay_y2 = overlay_y1 + (y2 - y1)

    alpha_overlay = overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2, 3] / 255.0
    alpha_face = 1.0 - alpha_overlay

    for c in range(0, 3):
        face_img[y1:y2, x1:x2, c] = (alpha_overlay * overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2, c] +
                                     alpha_face * face_img[y1:y2, x1:x2, c])

    return face_img



def find_best_match_vectorized(query_embedding, db_embeddings, employees):
    # Chuẩn hóa query
    query_norm = query_embedding / np.linalg.norm(query_embedding)

    # Convert tất cả embedding trong DB sang numpy array
    db_matrix = np.stack(db_embeddings)  # shape (n_samples, dim)
    db_matrix_norm = db_matrix / np.linalg.norm(db_matrix, axis=1, keepdims=True)

    # Tính cosine similarity 1 lần cho tất cả
    similarities = db_matrix_norm @ query_norm

    # Tìm chỉ số embedding có similarity cao nhất
    best_idx = np.argmax(similarities)
    best_score = similarities[best_idx]

    return best_idx, best_score









