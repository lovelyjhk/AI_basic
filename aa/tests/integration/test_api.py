from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "RL + Rust Backup MVP running" in r.json()["message"]

def test_detect_api():
    r = client.get("/detect")
    assert r.status_code == 200
    assert "accuracy" in r.json()
    assert "important_cols" in r.json()

def test_backup_api():
    r = client.get("/backup?emergency=1")
    assert r.status_code == 200
    assert "strategy" in r.json()
