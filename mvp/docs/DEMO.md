# MVP Localhost Demo

## Local (no Docker)

Prereqs: Python 3.13 available. The script uses in-memory fakeredis if Redis is not present.

1) Install deps (one-time):
- fastapi, uvicorn, redis, fakeredis, sqlalchemy, pydantic, python-multipart

2) Start services in three terminals or use below commands:

```bash
# Terminal 1 - Model
PYTHONPATH=$(pwd)/.. uvicorn mvp.model-svc.app:app --host 127.0.0.1 --port 58003
```

```bash
# Terminal 2 - EMR (SQLite) and PACS
PYTHONPATH=$(pwd)/.. uvicorn mvp.emr-api.app:app --host 127.0.0.1 --port 58001
# New terminal
PYTHONPATH=$(pwd)/.. uvicorn mvp.pacs-server.app:app --host 127.0.0.1 --port 58002
```

```bash
# Terminal 3 - Telemetry generator
python /workspace/mvp/telemetry-agent/agent.py
```

Health checks:
```bash
curl -s http://127.0.0.1:58001/health
curl -s http://127.0.0.1:58002/health
curl -s http://127.0.0.1:58003/health
```

## Trigger a risk and observe write-block

1) Generate high-risk telemetry:
```bash
FORCE_HIGH=1 SRC_IP=10.0.0.5 python /workspace/mvp/telemetry-agent/agent.py
```

2) Try EMR write from that IP (localhost demo uses client IP as 127.0.0.1). To simulate, directly set block key:
```bash
# In absence of Redis, the model service uses fakeredis; skip this in-memory step.
# Otherwise, set via redis-cli: HSET block_write 127.0.0.1 1
```

3) EMR write attempt:
```bash
curl -X POST 'http://127.0.0.1:58001/patients/P001/records' \
  -H 'Content-Type: application/json' \
  -d '{"patient_id":"P001","record":{"note":"test"}}'
```
- Expected: 403 when write-block is active; 200 otherwise.

4) PACS upload/download:
```bash
curl -F 'file=@/etc/hosts' http://127.0.0.1:58002/upload
curl -O http://127.0.0.1:58002/download/hosts
```

## Docker
Use `docker-compose.yml` in `mvp/` to bring up infra and services (requires Docker):
```bash
cd mvp
docker compose up -d --build
```
