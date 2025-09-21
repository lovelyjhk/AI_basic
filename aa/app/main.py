from fastapi import FastAPI
from app.services import rl_agent, rust_client
from app.models import detector

app = FastAPI()

@app.get("/")
def root():
    return {"message": "RL + Rust Backup MVP running"}

@app.get("/detect")
def detect_intrusion():
    acc, important = detector.train_and_detect()
    return {"accuracy": acc, "important_cols": important}

@app.get("/backup")
def backup_strategy(emergency: int = 0):
    strategy = rl_agent.choose_strategy(emergency)
    return {"emergency": emergency, "strategy": strategy}

@app.post("/encrypt")
def encrypt(data: list):
    encrypted = rust_client.encrypt_with_rust(data)
    return {"encrypted": encrypted}
