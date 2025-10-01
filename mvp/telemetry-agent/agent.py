import os, time, random
import redis
import fakeredis

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379")
try:
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
except Exception:
    r = fakeredis.FakeRedis(decode_responses=True)
STREAM = "telemetry"

if __name__ == "__main__":
    src_ip = os.getenv("SRC_IP","10.0.0.5")
    force_high = os.getenv("FORCE_HIGH","0") == "1"
    while True:
        if force_high:
            emr = 5500.8
            pacs = 550.8
            abn = 1
            una = 1
        else:
            emr = random.choice([35.1,45.2,60.3,5500.8])
            pacs = random.choice([10.2,25.6,550.8,2.1])
            abn = random.choice([0,0,1])
            una = random.choice([0,0,1])
        evt = {
            "source_ip": src_ip,
            "emr_tx_rate_sec": emr,
            "pacs_read_mb_sec": pacs,
            "abnormal_user_behavior": abn,
            "unauthorized_ip_access": una,
            "patient_ids": "[\"P001\"]"
        }
        r.xadd(STREAM, evt)
        time.sleep(1)
