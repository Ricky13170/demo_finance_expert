# Dockerfile - Đơn giản để chạy bot trong container
# 
# Giải thích từng bước:
# 1. Dùng Python 3.11 slim (nhẹ, đủ dùng)
# 2. Cài uv (package manager nhanh hơn pip)
# 3. Cài dependencies từ requirements.txt bằng uv
# 4. Copy code vào container
# 5. Chạy bot

FROM python:3.11-slim

# Đặt thư mục làm việc
WORKDIR /app

# Cài đặt uv (package manager nhanh hơn pip)
RUN pip install uv

# Copy requirements.txt trước để tận dụng Docker cache
COPY requirements.txt .

# Cài đặt packages bằng uv (nhanh hơn pip nhiều lần)
# uv tự động xử lý dependencies và tối ưu quá trình cài đặt
RUN uv pip install --system -r requirements.txt

# Copy code vào container
COPY src/ src/
COPY main.py .

# Chạy bot
CMD ["python", "main.py"]

