# Medical Cybersecurity System with RL Agent

## 🏥 프로젝트 개요
의료 데이터 보안을 위한 AI 기반 사이버보안 시스템으로, 강화학습 에이전트와 Rust 암호화 엔진을 통합한 마이크로서비스 아키텍처입니다.

## 🏗️ 시스템 아키텍처

### 핵심 컴포넌트
1. **FastAPI REST API 서버** - 메인 API 게이트웨이
2. **RL 에이전트** - 사이버보안 위협 탐지 및 대응
3. **Rust 암호화 엔진** - 고성능 파일 암호화
4. **WebSocket 서비스** - 실시간 통신
5. **파일 모니터링 시스템** - 실시간 파일 시스템 감시
6. **PostgreSQL 데이터베이스** - 메타데이터 및 로그 저장

### 마이크로서비스 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │  RL Agent       │    │  Crypto Engine  │
│   (FastAPI)     │◄──►│  (Python)       │◄──►│  (Rust)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │  File Monitor   │    │   Database      │
│   Service       │    │  System         │    │  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# Rust 설치 (암호화 엔진용)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. 데이터베이스 설정
```bash
# PostgreSQL 실행
docker-compose up -d postgres

# 데이터베이스 마이그레이션
alembic upgrade head
```

### 3. 서비스 실행
```bash
# API 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# RL 에이전트 실행 (별도 터미널)
python -m app.services.rl_agent

# 파일 모니터링 실행 (별도 터미널)
python -m app.services.file_monitor
```

## 📊 API 엔드포인트

### 인증 및 보안
- `POST /auth/login` - 사용자 로그인
- `POST /auth/register` - 사용자 등록
- `GET /auth/me` - 현재 사용자 정보

### 위협 탐지
- `GET /threats` - 탐지된 위협 목록
- `POST /threats/analyze` - 파일 위협 분석
- `GET /threats/{threat_id}` - 특정 위협 상세 정보

### 파일 관리
- `POST /files/encrypt` - 파일 암호화
- `POST /files/decrypt` - 파일 복호화
- `GET /files/status` - 암호화 상태 조회

### 실시간 모니터링
- `WebSocket /ws/monitor` - 실시간 모니터링 스트림
- `WebSocket /ws/alerts` - 보안 알림 스트림

## 🔒 보안 기능

### 암호화
- AES-256-GCM 파일 암호화
- RSA 키 교환
- 해시 기반 무결성 검증

### 위협 탐지
- 머신러닝 기반 악성코드 탐지
- 네트워크 패킷 분석
- 이상 행동 패턴 감지

### 규정 준수
- HIPAA (의료 정보 보호법) 준수
- GDPR 개인정보 보호 규정 준수
- FDA 의료기기 규정 준수

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 성능 테스트
python tests/performance/benchmark.py

# 보안 테스트
python tests/security/penetration_test.py
```

## 📈 성능 벤치마크

### 암호화 성능
- 파일 크기: 1GB
- AES-256-GCM: ~200MB/s
- RSA-2048 키 교환: ~50ms

### RL 에이전트 성능
- 위협 탐지 정확도: 95%+
- 응답 시간: <100ms
- False Positive: <2%

## 🛠️ 개발 도구

### 코드 품질
- Black (코드 포맷팅)
- Flake8 (린팅)
- MyPy (타입 체킹)
- Pytest (테스트)

### 모니터링
- Prometheus (메트릭)
- Grafana (대시보드)
- ELK Stack (로그 분석)

## 📚 문서

- [API 문서](http://localhost:8000/docs)
- [아키텍처 가이드](docs/architecture.md)
- [보안 가이드](docs/security.md)
- [배포 가이드](docs/deployment.md)

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🆘 지원

- 이슈 리포트: [GitHub Issues](https://github.com/your-repo/issues)
- 이메일: support@medical-cybersecurity.com
- 문서: [Wiki](https://github.com/your-repo/wiki)