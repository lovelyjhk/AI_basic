#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip

pushd emr-api >/dev/null
pip install -r requirements.txt
popd >/dev/null

pushd pacs-server >/dev/null
pip install -r requirements.txt
popd >/dev/null

pushd model-svc >/dev/null
pip install -r requirements.txt
popd >/dev/null

pushd telemetry-agent >/dev/null
pip install -r requirements.txt
popd >/dev/null

# Ensure storage dir exists
mkdir -p data/pacs

echo "Starting services locally (no docker) ..."

# Start model service
ENV REDIS_URL=${REDIS_URL:-redis://localhost:6379}
uvicorn model-svc.app:app --host 127.0.0.1 --port 58003 &

# Start EMR API (SQLite fallback) and PACS
DATABASE_URL=${DATABASE_URL:-sqlite+pysqlite:///./emr.db} \
uvicorn emr-api.app:app --host 127.0.0.1 --port 58001 &

STORAGE_PATH=$(pwd)/data/pacs \
uvicorn pacs-server.app:app --host 127.0.0.1 --port 58002 &

# Start telemetry agent
python telemetry-agent/agent.py &

echo "Services started:"
echo "- EMR API:       http://127.0.0.1:58001/health"
echo "- PACS Server:   http://127.0.0.1:58002/health"
echo "- Model Service: http://127.0.0.1:58003/health"
echo "- Telemetry:     streaming to fakeredis in-memory"

wait

