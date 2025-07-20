# AI 코딩 튜터 - 수익형 알고리즘 생성 앱

인공지능을 활용한 코딩 튜터 애플리케이션입니다. 사용자가 문제를 설명하면 AI가 다양한 프로그래밍 언어로 최적화된 알고리즘을 생성하고, 커뮤니티 평점 시스템을 통해 품질이 검증된 알고리즘들을 랭킹으로 제공합니다.

## 🚀 주요 기능

### 🤖 AI 기반 알고리즘 생성
- **다중 언어 지원**: Python, JavaScript, Java, C++, C, Go, Rust, V-lang 등 8개 언어
- **GPT-4 활용**: 최신 AI 모델을 통한 고품질 코드 생성
- **난이도별 최적화**: 쉬움, 보통, 어려움 단계별 맞춤 솔루션
- **복잡도 분석**: 시간/공간 복잡도 자동 계산 및 설명

### 🏆 커뮤니티 랭킹 시스템
- **평점 기반 랭킹**: 사용자 평가를 통한 알고리즘 품질 검증
- **실시간 순위**: 평점과 리뷰 수를 종합한 동적 랭킹
- **상세 평가**: 별점과 코멘트를 통한 피드백 시스템

### 👤 사용자 중심 기능
- **개인 대시보드**: 생성한 알고리즘 통계 및 관리
- **검색 및 필터링**: 언어, 난이도별 알고리즘 검색
- **코드 복사**: 원클릭 코드 클립보드 복사
- **반응형 UI**: 모바일부터 데스크톱까지 최적화된 인터페이스

## 🛠 기술 스택

### Backend
- **Flask**: Python 웹 프레임워크
- **SQLAlchemy**: ORM 및 데이터베이스 관리
- **JWT**: 사용자 인증 및 세션 관리
- **OpenAI API**: GPT-4 기반 코드 생성
- **SQLite/PostgreSQL**: 데이터베이스

### Frontend
- **React 18**: 모던 UI 라이브러리
- **React Router**: SPA 라우팅
- **Axios**: HTTP 클라이언트
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **React Syntax Highlighter**: 코드 하이라이팅
- **Lucide React**: 아이콘 라이브러리

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/ai-coding-tutor.git
cd ai-coding-tutor
```

### 2. 백엔드 설정
```bash
# Python 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp backend/.env.example backend/.env
# .env 파일에서 OpenAI API 키 등 설정
```

### 3. 프론트엔드 설정
```bash
# Node.js 의존성 설치
npm install

# Tailwind CSS 빌드
npm run build:css
```

### 4. 애플리케이션 실행
```bash
# 개발 모드 (프론트엔드 + 백엔드 동시 실행)
npm run dev

# 또는 별도 실행
# 백엔드 (터미널 1)
cd backend && python app.py

# 프론트엔드 (터미널 2)
npm start
```

### 5. 브라우저에서 확인
- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:5000

## 🔧 환경변수 설정

`backend/.env` 파일에 다음 값들을 설정하세요:

```env
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=sqlite:///coding_tutor.db
OPENAI_API_KEY=your-openai-api-key-here
FLASK_ENV=development
```

## 📱 주요 페이지

1. **홈페이지**: 서비스 소개 및 기능 안내
2. **알고리즘 생성**: AI를 통한 맞춤형 코드 생성
3. **랭킹**: 커뮤니티 평점 기반 알고리즘 순위
4. **대시보드**: 개인 통계 및 최근 활동
5. **내 알고리즘**: 생성한 알고리즘 관리 및 검색

## 🎯 사용법

### 1. 회원가입/로그인
- 이메일과 사용자명으로 간편 가입
- JWT 기반 안전한 인증 시스템

### 2. 알고리즘 생성
- 해결하고 싶은 문제를 자연어로 설명
- 원하는 프로그래밍 언어와 난이도 선택
- AI가 최적화된 코드와 상세한 설명 제공

### 3. 커뮤니티 참여
- 다른 사용자의 알고리즘에 평점과 리뷰 작성
- 랭킹을 통해 고품질 알고리즘 발견
- 자신의 알고리즘 개선을 위한 피드백 수집

## 💡 수익 모델

1. **프리미엄 구독**: 고급 AI 모델 및 무제한 생성
2. **광고 수익**: 타겟팅된 개발자 도구 광고
3. **API 서비스**: 기업용 알고리즘 생성 API 제공
4. **교육 콘텐츠**: 프리미엄 알고리즘 튜토리얼 판매

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**AI 코딩 튜터**로 더 나은 개발자가 되어보세요! 🚀 
