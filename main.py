from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import os

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL", "Not Set")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

class GeometryPayload(BaseModel):
    type: str
    coordinates: list[float]

@app.get("/health")
def health_check():
    return {"status": "Python Spatial Processor is running"}

@app.post("/snap")
def snap_geometry(payload: GeometryPayload):
    try:
        lng, lat = payload.coordinates
        
        # ปรับแก้ SQL: ให้แปลงพิกัด 4326 เป็น SRID เดียวกับเส้นท่อก่อนทำ Spatial Search
        # วิธีนี้จะทำให้ใช้ GIST Index ได้เต็มประสิทธิภาพ และไม่เกิด Error Mixed SRID
        query = text("""
            WITH target_point AS (
                SELECT ST_Transform(
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), 
                    (SELECT ST_SRID(wkb_geometry) FROM chonburi.b5531011_pipe LIMIT 1)
                ) AS geom
            ),
            closest_pipe AS (
                SELECT wkb_geometry 
                FROM chonburi.b5531011_pipe, target_point
                ORDER BY wkb_geometry <-> target_point.geom 
                LIMIT 1
            )
            SELECT 
                ST_X(ST_Transform(ST_ClosestPoint(closest_pipe.wkb_geometry, target_point.geom), 4326)) AS snap_lng,
                ST_Y(ST_Transform(ST_ClosestPoint(closest_pipe.wkb_geometry, target_point.geom), 4326)) AS snap_lat
            FROM closest_pipe, target_point;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"lng": lng, "lat": lat}).fetchone()
            
            if result:
                return {
                    "original": {"type": payload.type, "coordinates": payload.coordinates},
                    "snapped": {
                        "type": "Point",
                        "coordinates": [result.snap_lng, result.snap_lat]
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="No pipes found")
                
    except Exception as e:
        # พิมพ์ Error ออกทาง Console เพื่อให้เราไปเช็คใน Railway ได้
        print(f"❌ Python Snap Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))