"""
Medical Cybersecurity System - Main FastAPI Application
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.core.middleware import SecurityMiddleware, LoggingMiddleware
from app.core.exceptions import setup_exception_handlers

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("Starting Medical Cybersecurity System...")
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # 종료 시 실행
    logger.info("Shutting down Medical Cybersecurity System...")


# FastAPI 앱 생성
app = FastAPI(
    title="Medical Cybersecurity System",
    description="AI-powered cybersecurity system for medical data protection",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보안 미들웨어
app.add_middleware(SecurityMiddleware)

# 로깅 미들웨어
app.add_middleware(LoggingMiddleware)

# 신뢰할 수 있는 호스트 미들웨어
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 예외 핸들러 설정
setup_exception_handlers(app)

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

# 보안 스키마 설정
security = HTTPBearer()


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Medical Cybersecurity System API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "database": "connected",
            "redis": "connected",
            "rl_agent": "active",
            "crypto_engine": "active"
        }
    }


@app.get("/metrics")
async def metrics():
    """메트릭 엔드포인트 (Prometheus)"""
    # TODO: Prometheus 메트릭 구현
    return {"message": "Metrics endpoint"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info"
    )