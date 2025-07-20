# 🚀 AI 코딩 튜터 배포 가이드

이 문서는 AI 코딩 튜터 애플리케이션을 다양한 환경에 배포하는 방법을 안내합니다.

## 📋 배포 전 체크리스트

- [ ] OpenAI API 키 준비
- [ ] 도메인 준비 (선택사항)
- [ ] SSL 인증서 준비 (프로덕션)
- [ ] 데이터베이스 설정 (PostgreSQL 권장)
- [ ] 환경변수 설정

## 🔧 로컬 개발 환경

### 빠른 시작
```bash
# 저장소 클론
git clone <repository-url>
cd ai-coding-tutor

# 자동 설치 및 실행
./start.sh
```

### 수동 설치
```bash
# 1. Python 가상환경 설정
python -m venv backend/venv
source backend/venv/bin/activate  # Windows: backend\venv\Scripts\activate

# 2. Python 의존성 설치
pip install -r requirements.txt

# 3. Node.js 의존성 설치
npm install

# 4. 환경변수 설정
cp backend/.env.example backend/.env
# backend/.env 파일에서 OpenAI API 키 설정

# 5. 데이터베이스 초기화
cd backend
python -c "from app import app, db; app.app_context().push(); db.create_all()"
cd ..

# 6. 애플리케이션 실행
npm run dev
```

## 🌐 프로덕션 배포

### 1. Heroku 배포

#### 사전 준비
```bash
# Heroku CLI 설치 후
heroku login
heroku create your-app-name
```

#### 환경변수 설정
```bash
heroku config:set SECRET_KEY="your-production-secret-key"
heroku config:set JWT_SECRET_KEY="your-jwt-secret-key"
heroku config:set OPENAI_API_KEY="your-openai-api-key"
heroku config:set FLASK_ENV="production"
```

#### 배포 파일 생성
`Procfile` 생성:
```
web: gunicorn --chdir backend app:app
```

`runtime.txt` 생성:
```
python-3.11.0
```

#### 배포 실행
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### 2. Vercel 배포 (프론트엔드)

#### vercel.json 생성
```json
{
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://your-backend-url.herokuapp.com/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

#### 배포 실행
```bash
npm install -g vercel
vercel --prod
```

### 3. AWS EC2 배포

#### EC2 인스턴스 설정
```bash
# Ubuntu 20.04 LTS 기준
sudo apt update
sudo apt install python3 python3-pip nodejs npm nginx

# PM2 설치 (프로세스 관리)
sudo npm install -g pm2
```

#### 애플리케이션 설정
```bash
# 저장소 클론
git clone <repository-url>
cd ai-coding-tutor

# Python 의존성 설치
pip3 install -r requirements.txt

# Node.js 의존성 설치
npm install
npm run build

# 환경변수 설정
cp backend/.env.example backend/.env
# 프로덕션 값으로 수정

# 데이터베이스 초기화
cd backend
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
cd ..
```

#### PM2로 백엔드 실행
```bash
# ecosystem.config.js 생성
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'ai-coding-tutor-backend',
    script: 'backend/app.py',
    interpreter: 'python3',
    env: {
      FLASK_ENV: 'production'
    }
  }]
}
EOF

# PM2로 실행
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

#### Nginx 설정
```nginx
# /etc/nginx/sites-available/ai-coding-tutor
server {
    listen 80;
    server_name your-domain.com;

    # React 앱
    location / {
        root /path/to/ai-coding-tutor/build;
        try_files $uri $uri/ /index.html;
    }

    # API 프록시
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# Nginx 설정 활성화
sudo ln -s /etc/nginx/sites-available/ai-coding-tutor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Docker 배포

#### Dockerfile (백엔드)
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--host", "0.0.0.0", "--port", "5000", "app:app"]
```

#### Dockerfile (프론트엔드)
```dockerfile
# Dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=your-secret-key
      - JWT_SECRET_KEY=your-jwt-secret
      - OPENAI_API_KEY=your-openai-key
      - DATABASE_URL=postgresql://user:pass@db:5432/coding_tutor
    depends_on:
      - db

  frontend:
    build: .
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=coding_tutor
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Docker 실행
```bash
docker-compose up -d
```

## 🔒 보안 설정

### 환경변수 보안
- 프로덕션에서는 강력한 SECRET_KEY 사용
- OpenAI API 키는 절대 코드에 하드코딩하지 않음
- 데이터베이스 자격증명 보호

### HTTPS 설정
```bash
# Let's Encrypt SSL 인증서 (무료)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 방화벽 설정
```bash
# UFW 방화벽 설정
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## 📊 모니터링 및 로깅

### PM2 모니터링
```bash
pm2 monit              # 실시간 모니터링
pm2 logs               # 로그 확인
pm2 restart all        # 재시작
```

### Nginx 로그
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🔄 업데이트 및 배포 자동화

### GitHub Actions 예제
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.4
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /path/to/ai-coding-tutor
          git pull origin main
          pip install -r requirements.txt
          npm install
          npm run build
          pm2 restart all
```

## 🆘 트러블슈팅

### 일반적인 문제들

1. **OpenAI API 오류**
   - API 키가 올바른지 확인
   - API 사용량 한도 확인

2. **데이터베이스 연결 오류**
   - 데이터베이스 서비스 상태 확인
   - 연결 문자열 확인

3. **포트 충돌**
   - 다른 서비스가 같은 포트를 사용하는지 확인
   - `lsof -i :5000` 또는 `netstat -tulpn | grep :5000`

4. **권한 오류**
   - 파일 권한 확인: `chmod +x start.sh`
   - 디렉토리 소유권 확인

### 로그 확인 명령어
```bash
# 백엔드 로그
tail -f backend/app.log

# PM2 로그
pm2 logs

# Nginx 로그
sudo tail -f /var/log/nginx/error.log

# 시스템 로그
sudo journalctl -u nginx -f
```

## 📞 지원

배포 중 문제가 발생하면:
1. 이 문서의 트러블슈팅 섹션 확인
2. GitHub Issues에서 유사한 문제 검색
3. 새로운 이슈 생성 시 환경 정보와 에러 로그 포함

---

성공적인 배포를 위해 각 단계를 차근차근 따라해보세요! 🚀