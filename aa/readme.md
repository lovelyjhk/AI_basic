AI_basic/
├── app/
│   ├── main.py
│   ├── services/
│   │   ├── detector.py
│   │   ├── rl_agent.py
│   │   ├── rust_client.py
│   │   └── backup_strategy.py
├── rust_encrypt_server/
│   └── src/main.rs
│   └── Cargo.toml
├── tests/
│   ├── unit/
│   │   ├── test_detector.py
│   │   ├── test_backup_strategy.py
│   └── integration/
├── requirements.txt
├── README.md
├── .gitignore
└── .github/workflows/ci.yml



# 1. Python API 서버 실행
uvicorn app.main:app --reload --port 8000

# 2. RL 에이전트 학습 (최초 1회)
python -m app.services.rl_agent

# 3. Rust 암호화 서버 실행
cd rust_encrypt_server
cargo run


curl http://127.0.0.1:8000/detect
curl http://127.0.0.1:8000/backup?emergency=1
curl -X POST http://127.0.0.1:8000/encrypt -H "Content-Type: application/json" -d '{"records":[{"col1":123,"col2":456}]}'
