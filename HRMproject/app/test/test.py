
import face_recognition
from PIL import Image
import numpy as np
import requests
from io import BytesIO

def extract_face_embedding(image_url):
    try:
        print(f"🧾 Tải ảnh từ: {image_url}")
        response = requests.get(image_url)
        response.raise_for_status()

        pil_image = Image.open(BytesIO(response.content)).convert("RGB")
        print("📷 Kiểm tra mode:", pil_image.mode)

        image = np.array(pil_image).astype(np.uint8).copy()
        print("👀 Kiểm tra shape:", image.shape, "dtype:", image.dtype)

        face_locations = face_recognition.face_locations(image, model="hog")
        print("🔍 Số khuôn mặt tìm thấy:", len(face_locations))

        if not face_locations:
            print("❌ Không tìm thấy khuôn mặt nào")
            return None

        encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
        if not encodings:
            print("❌ Không trích xuất được face embedding")
            return None

        print("✅ Thành công, embedding size:", len(encodings[0]))
        return encodings[0]

    except Exception as e:
        print(f"❌ Lỗi extract_face_embedding: {e}")
        return None

if __name__ == "__main__":
    # Ảnh demo có khuôn mặt rõ ràng
    test_image_url = "https://res.cloudinary.com/dnzjjdg0v/image/upload/v1754492468/tkqnhfbn9uc5xsv7i2r6.jpg"
    embedding = extract_face_embedding(test_image_url)

    if embedding is not None:
        print("👉 Kết quả embedding (first 5 dims):", embedding[:5])
    else:
        print("⚠️ Test thất bại: Không có embedding.")
