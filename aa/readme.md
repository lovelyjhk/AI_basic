
---



```markdown
# 🛡️ RustSecurityAgent: RL + Rust Self-Lock Encryption MVP

## 📌 프로젝트 개요
본 프로젝트는 **강화학습 기반 Emergency 백업 정책**과  
**Rust 기반 Self-Lock 암호화 모듈**을 결합한 **의료 데이터 보안 솔루션 MVP**입니다.  

- 🧠 **침입 탐지**: RandomForest 기반 이상 탐지 + 중요 컬럼 추출  
- 🤖 **강화학습 에이전트 (RL)**: Emergency 상황에서 증분/전체 백업 전략 선택  
- 🔐 **Rust 암호화 서버**: XChaCha20-Poly1305 기반 암호화 API  
- 🌐 **FastAPI API 서버**: `/detect`, `/backup`, `/encrypt` 엔드포인트 제공  


## 📂 프로젝트 구조


AI\_basic/
├── app/
│   ├── main.py                # FastAPI API 서버
│   ├── services/
│   │   ├── detector.py        # 침입 탐지 + 중요 컬럼 추출
│   │   ├── backup\_strategy.py # RL 백업 정책
│   │   ├── rust\_client.py     # Rust 암호화 서버 연동
│   │   └── file\_monitor.py    # 파일 모니터링 (옵션)
│   └── models/                # ML 모델 정의
├── rust\_encrypt\_server/       # Rust 암호화 서버
│   ├── Cargo.toml
│   └── src/
│       └── main.rs
├── tests/
│   ├── unit/
│   │   ├── test\_detector.py
│   │   ├── test\_backup\_strategy.py
│   └── integration/
│       └── test\_api.py
├── requirements.txt
└── README.md

```
```

---
## ⚙️ 설치 및 실행 방법

### 1. Python 환경 준비
```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
````

### 2. Rust 암호화 서버 실행

```bash
cd rust_encrypt_server
cargo run
```

> 실행 후: `http://127.0.0.1:8080/encrypt` REST API 구동

### 3. FastAPI 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

> 실행 후: `http://127.0.0.1:8000/docs` 에서 Swagger 문서 확인 가능

### 4. RL 에이전트 학습 (최초 1회)

```bash
python -m app.services.backup_strategy
```

---

## 🔑 주요 API 엔드포인트

* **침입 탐지**

  * `GET /detect` → 탐지 정확도 + 중요 컬럼 반환
* **백업 전략**

  * `GET /backup?emergency=0` → Full / Incremental 결정
* **암호화**

  * `POST /encrypt` → Rust 서버 호출, 암호화 결과 반환

---

## 🧪 테스트

단위/통합 테스트 실행:

```bash
pytest -v
```

---

## 📊 성능 목표 (MVP 기준)

* 탐지 정확도: **80% 이상**
* RL 에이전트: Emergency 상황에서 Incremental 전략 선택률 ≥ 95%
* 암호화 성능: 200MB/s 이상 (AES-256-GCM 벤치마크 기준)

---

## 📜 라이선스

MIT License (또는 저장소 설정에 따른 라이선스 참고)

```

---
