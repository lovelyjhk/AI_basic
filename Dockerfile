FROM python:3.11-slim

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Rust 설치 (암호화 엔진용)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Rust 프로젝트 설정 (암호화 엔진)
COPY rust_crypto/ ./rust_crypto/
WORKDIR /app/rust_crypto
RUN cargo build --release

# 메인 앱으로 돌아가기
WORKDIR /app

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# 데이터 디렉토리 생성
RUN mkdir -p /app/data /app/logs /app/monitor

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 기본 명령어
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]