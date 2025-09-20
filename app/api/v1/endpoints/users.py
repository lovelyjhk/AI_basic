"""
User management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user, get_password_hash
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserResponse, UserCreate, UserUpdate, RoleResponse
from app.schemas.auth import UserResponse as AuthUserResponse

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    """사용자 목록 조회 (관리자만)"""
    
    # 관리자 권한 확인
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    query = db.query(User)
    
    # 필터링
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.offset(skip).limit(limit).all()
    
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            role=user.role.name if user.role else None,
            created_at=user.created_at,
            last_login=user.last_login
        )
        for user in users
    ]


@router.get("/me", response_model=AuthUserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> AuthUserResponse:
    """현재 사용자 정보 조회"""
    
    return AuthUserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        role=current_user.role.name if current_user.role else None
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """특정 사용자 정보 조회"""
    
    # 본인 또는 관리자만 조회 가능
    if current_user.id != user_id and (not current_user.role or current_user.role.name != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        role=user.role.name if user.role else None,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """사용자 정보 업데이트"""
    
    # 본인 또는 관리자만 수정 가능
    if current_user.id != user_id and (not current_user.role or current_user.role.name != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 업데이트할 필드들
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        role=user.role.name if user.role else None,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """사용자 삭제 (관리자만)"""
    
    # 관리자 권한 확인
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    # 본인 삭제 방지
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/roles/", response_model=List[RoleResponse])
async def get_roles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[RoleResponse]:
    """역할 목록 조회"""
    
    roles = db.query(Role).all()
    
    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=role.permissions.split(',') if role.permissions else [],
            created_at=role.created_at
        )
        for role in roles
    ]


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """사용자 활성화 (관리자만)"""
    
    # 관리자 권한 확인
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """사용자 비활성화 (관리자만)"""
    
    # 관리자 권한 확인
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    # 본인 비활성화 방지
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "User deactivated successfully"}


@router.get("/{user_id}/statistics")
async def get_user_statistics(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """사용자 통계 조회"""
    
    # 본인 또는 관리자만 조회 가능
    if current_user.id != user_id and (not current_user.role or current_user.role.name != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # TODO: 실제 통계 계산 구현
    statistics = {
        "user_id": user_id,
        "files_uploaded": 0,
        "files_encrypted": 0,
        "threats_detected": 0,
        "last_activity": user.last_login.isoformat() if user.last_login else None,
        "account_created": user.created_at.isoformat()
    }
    
    return statistics