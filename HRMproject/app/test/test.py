
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
    
import insightface

# Load model ArcFace
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
            # print("❌ Không tìm thấy khuôn mặt")
            # return None
            print("⚠️ ArcFace không detect, fallback sang face_recognition...")
            # Detect bằng face_recognition
            image = np.array(img).astype(np.uint8).copy()
            locations = face_recognition.face_locations(image, model="hog")
            if not locations:
                print("❌ Không tìm thấy khuôn mặt nào")
                return None
            # Crop khuôn mặt lớn nhất
            top, right, bottom, left = locations[0]
            face_img = img[top:bottom, left:right]

            # Gửi lại cho ArcFace để lấy embedding
            faces = model.get(face_img)
            if len(faces) == 0:
                print("❌ ArcFace vẫn không lấy được embedding")
                return None

        # InsightFace cho embedding 512 chiều
        embedding = faces[0].embedding
        return embedding

    except Exception as e:
        print(f"❌ Lỗi extract_face_embedding: {e}")
        return None


if __name__ == "__main__":
    # Ảnh demo có khuôn mặt rõ ràng
    test_image_url = "https://movieplayer.net-cdn.it/images/2008/10/24/nathan-lane-guest-star-in-til-death-93776.jpg"
    # test_image_url = "https://res.cloudinary.com/dnzjjdg0v/image/upload/v1757388172/k70j81qu2h8fxbqylzd5.png"
    embedding = extract_face_embedding_ArcFace(test_image_url)
    # embedding = extract_face_embedding(test_image_url)

    if embedding is not None:
        print("👉 Kết quả embedding (first 5 dims):", embedding[:5])
    else:
        print("⚠️ Test thất bại: Không có embedding.")
