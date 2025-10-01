from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os, shutil
import redis
import fakeredis

DEFAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STORAGE_PATH = os.getenv("STORAGE_PATH", os.path.join(DEFAULT_ROOT, "data", "pacs"))
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379")
app = FastAPI(title="PACS Server", version="0.1.0")

os.makedirs(STORAGE_PATH, exist_ok=True)
try:
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
except Exception:
    r = fakeredis.FakeRedis(decode_responses=True)

@app.get("/health")
async def health():
    return {"status":"ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if os.environ.get("READ_ONLY","0") == "1" or r.get("pacs_read_only") == "1":
        raise HTTPException(status_code=403, detail="read-only mode")
    dest = os.path.join(STORAGE_PATH, file.filename)
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    return {"status":"uploaded","file": file.filename}

@app.get("/download/{name}")
async def download(name: str):
    path = os.path.join(STORAGE_PATH, name)
    if not os.path.exists(path):
        raise HTTPException(404, "not found")
    return FileResponse(path)
