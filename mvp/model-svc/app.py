import os, asyncio
from fastapi import FastAPI
import redis.asyncio as aioredis
import fakeredis.aioredis as fake_aioredis

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379")
async def get_redis():
    try:
        client = aioredis.from_url(REDIS_URL, decode_responses=True)
        await client.ping()
        return client
    except Exception:
        return fake_aioredis.FakeRedis(decode_responses=True)

STREAM_IN = "telemetry"
STREAM_OUT = "risk.alerts"

app = FastAPI(title="Model Service", version="0.1.0")

@app.get("/health")
async def health():
    return {"status":"ok"}

async def score_event(evt):
    emr = float(evt.get("emr_tx_rate_sec", 0))
    pacs = float(evt.get("pacs_read_mb_sec", 0))
    abn = int(evt.get("abnormal_user_behavior", 0))
    una = int(evt.get("unauthorized_ip_access", 0))
    score = (emr/3000.0) + (pacs/400.0) + (abn*0.7) + (una*0.9)
    return min(1.0, score)

async def run():
    global r
    r = await get_redis()
    last_id = "$"
    while True:
        resp = await r.xread({STREAM_IN: last_id}, block=1000, count=10)
        if not resp:
            continue
        for stream, messages in resp:
            for msg_id, fields in messages:
                last_id = msg_id
                score = await score_event(fields)
                if score >= 0.7:
                    alert = {"source_ip": fields.get("source_ip","unknown"), "severity":"block", "reason":"high_risk", "patient_ids": fields.get("patient_ids","[]")}
                    await r.xadd(STREAM_OUT, alert)

@app.on_event("startup")
async def startup():
    asyncio.create_task(run())
