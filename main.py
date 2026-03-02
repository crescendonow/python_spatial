from fastapi import FastAPI
import os

app = FastAPI()

# รับค่า Database URL เผื่อต้องต่อ PostGIS โดยตรง
db_url = os.getenv("DATABASE_URL", "Not Set")

@app.get("/health")
def health_check():
    return {
        "service": "Python Spatial Processor",
        "status": "OK",
        "db_connected": db_url != "Not Set"
    }

@app.post("/snap")
def snap_geometry(payload: dict):
    # โค้ดสำหรับรับ GeoJSON และใช้ Shapely/GeoPandas จะอยู่ตรงนี้
    return {"message": "Geometry snapped successfully", "data": payload}