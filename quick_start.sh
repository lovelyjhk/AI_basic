#!/bin/bash

# ============================================================
# 의료 사이버보안 AI-Rust 방어 시스템
# 빠른 시작 스크립트
# ============================================================

set -e  # 에러 발생 시 중단

echo "=========================================="
echo "석사 논문 프로젝트 빠른 시작"
echo "=========================================="
echo ""

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Rust 설치 확인
echo -e "${BLUE}[1/5] Rust 설치 확인...${NC}"
if ! command -v cargo &> /dev/null; then
    echo -e "${YELLOW}Rust가 설치되어 있지 않습니다. 설치를 진행합니다...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
    echo -e "${GREEN}✓ Rust 설치 완료${NC}"
else
    echo -e "${GREEN}✓ Rust가 이미 설치되어 있습니다 ($(rustc --version))${NC}"
fi

# 2. Python 가상환경 생성
echo ""
echo -e "${BLUE}[2/5] Python 가상환경 설정...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ 가상환경 생성 완료${NC}"
else
    echo -e "${YELLOW}가상환경이 이미 존재합니다.${NC}"
fi

# 가상환경 활성화
source venv/bin/activate

# 3. Python 의존성 설치
echo ""
echo -e "${BLUE}[3/5] Python 패키지 설치...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo -e "${GREEN}✓ Python 패키지 설치 완료${NC}"

# 4. Rust 프로젝트 빌드
echo ""
echo -e "${BLUE}[4/5] Rust 프로젝트 빌드...${NC}"
cd rust_crypto
cargo build --release
echo -e "${GREEN}✓ Rust 빌드 완료${NC}"
cd ..

# 5. 디렉토리 생성
echo ""
echo -e "${BLUE}[5/5] 필수 디렉토리 생성...${NC}"
mkdir -p models
mkdir -p simulation_data/medical
mkdir -p benchmark_results
echo -e "${GREEN}✓ 디렉토리 생성 완료${NC}"

# 완료 메시지
echo ""
echo -e "${GREEN}=========================================="
echo "환경 설정 완료! 🎉"
echo "==========================================${NC}"
echo ""
echo "다음 단계:"
echo ""
echo "1️⃣  AI 모델 학습:"
echo "   python ai_predictor.py"
echo ""
echo "2️⃣  통합 벤치마크 실행:"
echo "   python main_benchmark.py"
echo ""
echo "3️⃣  의료 데이터 시뮬레이션:"
echo "   python medical_simulator.py"
echo ""
echo "📚 자세한 내용은 README.md를 참조하세요."
echo ""
