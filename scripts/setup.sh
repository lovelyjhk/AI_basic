#!/bin/bash

# Medical Cybersecurity System Setup Script

set -e

echo "🏥 Medical Cybersecurity System Setup"
echo "======================================"

# Python 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Python 의존성 설치
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Rust 설치 확인
if ! command -v cargo &> /dev/null; then
    echo "🦀 Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source ~/.cargo/env
fi

# Rust 암호화 엔진 빌드
echo "🔐 Building Rust crypto engine..."
cd rust_crypto
cargo build --release
cd ..

# 데이터베이스 초기화
echo "🗄️ Initializing database..."
alembic upgrade head

# 필요한 디렉토리 생성
echo "📁 Creating necessary directories..."
mkdir -p /app/data
mkdir -p /app/logs
mkdir -p /app/models
mkdir -p /app/monitor
mkdir -p /app/temp
mkdir -p /app/quarantine

# 권한 설정
echo "🔒 Setting up permissions..."
chmod 755 /app/data
chmod 755 /app/logs
chmod 755 /app/models
chmod 755 /app/monitor
chmod 755 /app/temp
chmod 755 /app/quarantine

# 환경 변수 파일 생성
echo "⚙️ Creating environment configuration..."
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/medical_cybersecurity

# Security Configuration
SECRET_KEY=your-secret-key-change-in-production-32-chars-long
CRYPTO_MASTER_KEY=your-crypto-master-key-32-chars-long

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Environment
ENVIRONMENT=development
DEBUG=true

# HIPAA Compliance
HIPAA_COMPLIANCE=true
AUDIT_LOGGING=true
EOF

echo "✅ Setup completed successfully!"
echo ""
echo "🚀 To start the system:"
echo "   python scripts/start_services.py"
echo ""
echo "🧪 To run tests:"
echo "   python -m pytest tests/"
echo ""
echo "📊 To view monitoring dashboard:"
echo "   http://localhost:8000/api/v1/monitoring/dashboard"