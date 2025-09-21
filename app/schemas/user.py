"""
User schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    email: EmailStr
    username: str
    is_active: bool = True


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str


class UserUpdate(BaseModel):
    """사용자 업데이트 스키마"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """데이터베이스 사용자 스키마"""
    id: int
    hashed_password: str
    role_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class User(UserBase):
    """사용자 응답 스키마"""
    id: int
    role: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """역할 기본 스키마"""
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


class RoleCreate(RoleBase):
    """역할 생성 스키마"""
    pass


class RoleUpdate(BaseModel):
    """역할 업데이트 스키마"""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class Role(RoleBase):
    """역할 응답 스키마"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True