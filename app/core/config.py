"""
Application Configuration Settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    APP_NAME: str = "Medical Cybersecurity System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/medical_cybersecurity"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis 설정
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_POOL_SIZE: int = 10
    
    # JWT 설정
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 암호화 설정
    ENCRYPTION_KEY: str = "your-encryption-key-32-chars-long"
    ENCRYPTION_ALGORITHM: str = "AES-256-GCM"
    
    # 파일 모니터링 설정
    MONITOR_DIRECTORIES: List[str] = ["/monitor", "/data"]
    MONITOR_FILE_EXTENSIONS: List[str] = [".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx"]
    MAX_FILE_SIZE_MB: int = 100
    
    # RL 에이전트 설정
    RL_MODEL_PATH: str = "/app/models/rl_agent.pkl"
    RL_TRAINING_EPISODES: int = 1000
    RL_LEARNING_RATE: float = 0.001
    
    # 보안 설정
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    SESSION_TIMEOUT_MINUTES: int = 30
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/app/logs/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    # 모니터링 설정
    PROMETHEUS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    
    # HIPAA 준수 설정
    HIPAA_COMPLIANCE: bool = True
    AUDIT_LOGGING: bool = True
    DATA_RETENTION_DAYS: int = 2555  # 7년
    
    # 성능 설정
    MAX_WORKERS: int = 4
    REQUEST_TIMEOUT: int = 30
    RESPONSE_TIMEOUT: int = 30
    
    # 개발 설정
    RELOAD: bool = True
    WORKERS: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()

# 디렉토리 생성
def create_directories():
    """필요한 디렉토리 생성"""
    directories = [
        "/app/data",
        "/app/logs", 
        "/app/models",
        "/app/monitor",
        "/app/temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# 애플리케이션 시작 시 디렉토리 생성
create_directories()