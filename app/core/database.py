"""
Database Configuration and Session Management
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
from typing import Generator

from app.core.config import settings

logger = logging.getLogger(__name__)

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스
Base = declarative_base()

# 메타데이터
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """데이터베이스 초기화"""
    try:
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # 초기 데이터 삽입 (필요한 경우)
        await create_initial_data()
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def create_initial_data():
    """초기 데이터 생성"""
    from app.models.user import User
    from app.models.role import Role
    from app.core.security import get_password_hash
    
    db = SessionLocal()
    try:
        # 기본 역할 생성
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(
                name="admin",
                description="System Administrator",
                permissions=["*"]
            )
            db.add(admin_role)
        
        user_role = db.query(Role).filter(Role.name == "user").first()
        if not user_role:
            user_role = Role(
                name="user", 
                description="Regular User",
                permissions=["read", "write"]
            )
            db.add(user_role)
        
        # 기본 관리자 사용자 생성
        admin_user = db.query(User).filter(User.email == "admin@medical-cybersecurity.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@medical-cybersecurity.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                role_id=admin_role.id
            )
            db.add(admin_user)
        
        db.commit()
        logger.info("Initial data created successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create initial data: {e}")
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """데이터베이스 세션 직접 반환"""
    return SessionLocal()