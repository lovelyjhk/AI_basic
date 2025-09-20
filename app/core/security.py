"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 토큰 스키마
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """리프레시 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """토큰 검증"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """현재 사용자 가져오기"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """현재 활성 사용자 가져오기"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def check_permissions(user: User, required_permission: str) -> bool:
    """권한 확인"""
    if not user.role:
        return False
    
    # 관리자는 모든 권한
    if "*" in user.role.permissions:
        return True
    
    # 특정 권한 확인
    return required_permission in user.role.permissions


def require_permission(permission: str):
    """권한 필요 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # TODO: 권한 확인 로직 구현
            return func(*args, **kwargs)
        return wrapper
    return decorator


class SecurityManager:
    """보안 관리자"""
    
    def __init__(self):
        self.failed_attempts = {}
        self.locked_users = {}
    
    def record_failed_login(self, email: str):
        """실패한 로그인 기록"""
        if email not in self.failed_attempts:
            self.failed_attempts[email] = 0
        
        self.failed_attempts[email] += 1
        
        if self.failed_attempts[email] >= settings.MAX_LOGIN_ATTEMPTS:
            self.locked_users[email] = datetime.utcnow()
    
    def is_user_locked(self, email: str) -> bool:
        """사용자 잠금 상태 확인"""
        if email not in self.locked_users:
            return False
        
        lockout_time = self.locked_users[email]
        if datetime.utcnow() - lockout_time > timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES):
            # 잠금 해제
            del self.locked_users[email]
            if email in self.failed_attempts:
                del self.failed_attempts[email]
            return False
        
        return True
    
    def reset_failed_attempts(self, email: str):
        """실패 시도 초기화"""
        if email in self.failed_attempts:
            del self.failed_attempts[email]
        if email in self.locked_users:
            del self.locked_users[email]


# 전역 보안 관리자
security_manager = SecurityManager()