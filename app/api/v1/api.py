"""
Main API router for v1
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, threats, files, monitoring, users

api_router = APIRouter()

# 인증 관련 엔드포인트
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# 사용자 관리 엔드포인트
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 위협 탐지 엔드포인트
api_router.include_router(threats.router, prefix="/threats", tags=["threats"])

# 파일 관리 엔드포인트
api_router.include_router(files.router, prefix="/files", tags=["files"])

# 모니터링 엔드포인트
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])