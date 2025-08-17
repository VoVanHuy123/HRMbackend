# Sử dụng Python 3.11 làm base image
# FROM python:3.12-slim
FROM python:3.11-slim


# Đặt biến môi trường để tránh Python lưu cache
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tạo thư mục trong container để chứa code
WORKDIR /app

# # Cài đặt dependencies hệ thống (nếu cần, ví dụ psycopg2, mysqlclient...)
# RUN apt-get update && apt-get install -y \
#     gcc \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# Cài các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y \
        build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev \
        default-libmysqlclient-dev pkg-config \
        libpq-dev python3-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Thêm sau các lệnh RUN trong Dockerfile:
RUN apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# Copy file requirements trước để cache khi build
COPY requirements-cicd.txt /app/

# Cài đặt dependencies Python
RUN pip install --no-cache-dir -r requirements-cicd.txt

# Copy toàn bộ project vào container
COPY . /app/

# Tạo thư mục staticfiles trước khi collectstatic
RUN mkdir -p /app/staticfiles

# Collect static files (nếu bạn dùng Django static)
RUN python manage.py collectstatic --noinput

# # Chạy ứng dụng với Gunicorn (thay myproject.wsgi bằng tên app của bạn)
# CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
# Lệnh chạy Daphne
CMD ["sh","-c","daphne -b 0.0.0.0 -p $PORT HRMproject.asgi:application"]
