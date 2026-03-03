from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import os

app = FastAPI()

# 1. จัดการ Database URL อัตโนมัติ (เปลี่ยน postgres:// เป็น postgresql://)
DATABASE_URL = os.getenv("DATABASE_URL", "Not Set")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# สร้างการเชื่อมต่อฐานข้อมูล
engine = create_engine(DATABASE_URL)

# 2. กำหนดโครงสร้างข้อมูลที่รับเข้ามาจาก Go API
class GeometryPayload(BaseModel):
    type: str
    coordinates: list[float]

@app.get("/health")
def health_check():
    return {"status": "Python Spatial Processor is running"}

# 3. Endpoint สำหรับทำ Snap ไปติดท่อประปา
@app.post("/snap")
def snap_geometry(payload: GeometryPayload):
    try:
        lng, lat = payload.coordinates
        
        # คำสั่ง SQL สุดทรงพลังของ PostGIS ในการหาจุดที่ใกล้ที่สุดบนเส้นท่อประปา
        query = text("""
            WITH closest_pipe AS (
                SELECT wkb_geometry 
                FROM chonburi.b5531011_pipe 
                ORDER BY wkb_geometry <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326) 
                LIMIT 1
            )
            SELECT 
                ST_X(ST_ClosestPoint(wkb_geometry, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))) AS snap_lng,
                ST_Y(ST_ClosestPoint(wkb_geometry, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))) AS snap_lat
            FROM closest_pipe;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"lng": lng, "lat": lat}).fetchone()
            
            if result:
                return {
                    "original": payload.dict(),
                    "snapped": {
                        "type": "Point",
                        "coordinates": [result.snap_lng, result.snap_lat]
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="No pipes found")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))