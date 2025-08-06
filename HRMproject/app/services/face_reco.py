import numpy as np
# from services.face_reco import extract_face_embedding
from facerecognition.models import FaceTrainingImage
import face_recognition
import numpy as np
from PIL import Image
import requests
from io import BytesIO



def extract_face_embedding(image_or_url):
    try:
        if isinstance(image_or_url, str):
            print("🧾 Đang tải ảnh từ URL:", image_or_url)
            response = requests.get(image_or_url)
            response.raise_for_status()

            # Mở bằng PIL, convert về RGB
            pil_image = Image.open(BytesIO(response.content)).convert("RGB")
            print("📷 Định dạng ảnh:", pil_image.mode)

            # Chuyển sang numpy array và ép kiểu uint8
            # sau khi convert về RGB
            image = np.array(pil_image).copy()

            # check shape
            print("👀 Kiểm tra shape:", image.shape, "dtype:", image.dtype)

            if image.dtype != np.uint8:
                print("❗ Force cast dtype")
                image = image.astype(np.uint8)

            if len(image.shape) == 2:
                print("❗ Ảnh gray, mở rộng thành RGB")
                image = np.stack([image]*3, axis=-1)
            elif image.shape[2] == 4:
                print("❗ Ảnh có alpha channel, bỏ alpha")
                image = image[:, :, :3]
        elif isinstance(image_or_url, Image.Image):
            print("🧾 Chuyển đổi từ PIL Image sang numpy array")
            image = np.array(image_or_url.convert("RGB")).astype(np.uint8).copy()
        else:
            print("❌ Định dạng ảnh không hợp lệ")
            return None

        # Nhận diện khuôn mặt
        face_locations = face_recognition.face_locations(image, model="hog")
        print("🔍 Số khuôn mặt tìm thấy:", len(face_locations))

        if not face_locations or len(face_locations) == 0:
            print("❌ Không tìm thấy khuôn mặt nào")
            return None

        encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
        if not encodings:
            print("❌ Không trích xuất được embedding")
            return None

        print("✅ Trích xuất thành công embedding")
        return encodings[0]

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

if __name__ == "__main__":
    # Ảnh demo có khuôn mặt rõ ràng
    test_image_url = "https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/obama.jpg"
    embedding = extract_face_embedding(test_image_url)

    if embedding is not None:
        print("👉 Kết quả embedding (first 5 dims):", embedding[:5])
    else:
        print("⚠️ Test thất bại: Không có embedding.")