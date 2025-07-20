#!/bin/bash

echo "🚀 AI 코딩 튜터 애플리케이션을 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python 가상환경 확인 및 생성
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}Python 가상환경을 생성합니다...${NC}"
    python3 -m venv backend/venv
fi

# 가상환경 활성화
echo -e "${BLUE}Python 가상환경을 활성화합니다...${NC}"
source backend/venv/bin/activate

# Python 의존성 설치
echo -e "${BLUE}Python 의존성을 설치합니다...${NC}"
pip install -r requirements.txt

# Node.js 의존성 설치
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Node.js 의존성을 설치합니다...${NC}"
    npm install
fi

# 환경변수 파일 확인
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}환경변수 파일을 복사합니다...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${RED}⚠️  backend/.env 파일에서 OpenAI API 키를 설정해주세요!${NC}"
fi

# 데이터베이스 초기화
echo -e "${BLUE}데이터베이스를 초기화합니다...${NC}"
cd backend
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ 데이터베이스가 초기화되었습니다.')"
cd ..

echo -e "${GREEN}✅ 설정이 완료되었습니다!${NC}"
echo -e "${GREEN}🌐 애플리케이션을 실행합니다...${NC}"
echo ""
echo -e "${YELLOW}📝 사용법:${NC}"
echo -e "  - 프론트엔드: ${BLUE}http://localhost:3000${NC}"
echo -e "  - 백엔드 API: ${BLUE}http://localhost:5000${NC}"
echo ""
echo -e "${YELLOW}⚠️  주의사항:${NC}"
echo -e "  - backend/.env 파일에 OpenAI API 키를 설정해야 AI 기능이 작동합니다"
echo -e "  - Ctrl+C로 종료할 수 있습니다"
echo ""

# 개발 서버 실행
npm run dev