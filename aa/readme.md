# 1. Python API 서버 실행
uvicorn app.main:app --reload --port 8000

# 2. RL 에이전트 학습 (최초 1회)
python -m app.services.rl_agent

# 3. Rust 암호화 서버 실행
cd rust_encrypt_server
cargo run
