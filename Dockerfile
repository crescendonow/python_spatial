FROM python:3.11-slim

# ติดตั้งไลบรารีระบบพื้นฐานที่ Geopandas และ PostGIS ต้องการ
RUN apt-get update && apt-get install -y \
    libgdal-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# เปิด Port 8000 สำหรับใช้งานใน Railway
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]