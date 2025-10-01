from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import os, json
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine import Engine
import redis.asyncio as aioredis
import fakeredis.aioredis as fake_aioredis

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+pysqlite:///./emr.db")
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379")

app = FastAPI(title="EMR API", version="0.1.0")
engine: Engine = sa.create_engine(DATABASE_URL, pool_pre_ping=True)
try:
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    r = fake_aioredis.FakeRedis(decode_responses=True)

class EMRRecord(BaseModel):
    patient_id: str
    record: dict

@app.get("/health")
async def health():
    return {"status":"ok"}

@app.on_event("startup")
async def startup():
    # create tables if using sqlite
    if DATABASE_URL.startswith("sqlite"):
        with engine.begin() as conn:
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS emr_records (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  patient_id TEXT NOT NULL,
                  record JSON NOT NULL,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            ))

@app.get("/patients/{patient_id}/records")
async def list_records(patient_id: str):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, record, created_at FROM emr_records WHERE patient_id=:pid ORDER BY id DESC"), {"pid": patient_id}).mappings().all()
        return [{"id": row["id"], "record": row["record"], "created_at": str(row["created_at"])} for row in rows]

@app.post("/patients/{patient_id}/records")
async def create_record(patient_id: str, rec: EMRRecord, request: Request):
    # Prefer real client IP via X-Forwarded-For (proxied by NGINX)
    xff = request.headers.get("x-forwarded-for")
    ip = xff.split(",")[0].strip() if xff else request.client.host
    if await r.hget("block_write", ip):
        raise HTTPException(status_code=403, detail="write blocked")
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO emr_records (patient_id, record) VALUES (:pid, :rec::jsonb)"),
            {"pid": patient_id, "rec": json.dumps(rec.record)}
        )
    return {"status":"created"}
