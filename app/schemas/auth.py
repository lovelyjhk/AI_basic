"""
Authentication schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """회원가입 요청 스키마"""
    email: EmailStr
    username: str
    password: str


class Token(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    email: str
    username: str
    is_active: bool
    role: Optional[str] = None
    
    class Config:
        from_attributes = True