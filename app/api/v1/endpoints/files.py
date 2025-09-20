"""
File management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import shutil
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.file import File as FileModel, FileAccessLog
from app.schemas.file import (
    FileResponse, 
    FileCreate, 
    FileUpdate,
    EncryptionRequest,
    EncryptionResponse,
    FileAccessLogResponse
)
from app.services.crypto_engine import get_crypto_engine

router = APIRouter()


@router.get("/", response_model=List[FileResponse])
async def get_files(
    skip: int = 0,
    limit: int = 100,
    is_encrypted: Optional[bool] = None,
    sensitivity_level: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[FileResponse]:
    """파일 목록 조회"""
    
    query = db.query(FileModel)
    
    # 필터링
    if is_encrypted is not None:
        query = query.filter(FileModel.is_encrypted == is_encrypted)
    if sensitivity_level:
        query = query.filter(FileModel.sensitivity_level == sensitivity_level)
    
    files = query.offset(skip).limit(limit).all()
    
    return [
        FileResponse(
            id=file.id,
            file_id=file.file_id,
            original_name=file.original_name,
            file_path=file.file_path,
            file_hash=file.file_hash,
            file_size=file.file_size,
            mime_type=file.mime_type,
            is_encrypted=file.is_encrypted,
            encryption_algorithm=file.encryption_algorithm,
            is_sensitive=file.is_sensitive,
            sensitivity_level=file.sensitivity_level,
            classification=file.classification,
            status=file.status,
            created_at=file.created_at,
            updated_at=file.updated_at,
            last_accessed=file.last_accessed
        )
        for file in files
    ]


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> FileResponse:
    """특정 파일 정보 조회"""
    
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # 접근 로그 기록
    access_log = FileAccessLog(
        access_type="read",
        access_result="success",
        file_id=file.id,
        user_id=current_user.id
    )
    db.add(access_log)
    db.commit()
    
    return FileResponse(
        id=file.id,
        file_id=file.file_id,
        original_name=file.original_name,
        file_path=file.file_path,
        file_hash=file.file_hash,
        file_size=file.file_size,
        mime_type=file.mime_type,
        is_encrypted=file.is_encrypted,
        encryption_algorithm=file.encryption_algorithm,
        is_sensitive=file.is_sensitive,
        sensitivity_level=file.sensitivity_level,
        classification=file.classification,
        status=file.status,
        created_at=file.created_at,
        updated_at=file.updated_at,
        last_accessed=file.last_accessed
    )


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sensitivity_level: str = "internal",
    classification: str = "general",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> FileResponse:
    """파일 업로드"""
    
    try:
        # 파일 저장 경로 생성
        upload_dir = Path("/app/data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 파일 해시 계산
        import hashlib
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # 데이터베이스에 파일 정보 저장
        file_model = FileModel(
            file_id=f"file_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            original_name=file.filename,
            file_path=str(file_path),
            file_hash=file_hash,
            file_size=file_path.stat().st_size,
            mime_type=file.content_type,
            is_sensitive=sensitivity_level in ["confidential", "restricted"],
            sensitivity_level=sensitivity_level,
            classification=classification,
            user_id=current_user.id
        )
        
        db.add(file_model)
        db.commit()
        db.refresh(file_model)
        
        # 백그라운드에서 위협 분석 실행
        background_tasks.add_task(analyze_uploaded_file, str(file_path), file_hash)
        
        return FileResponse(
            id=file_model.id,
            file_id=file_model.file_id,
            original_name=file_model.original_name,
            file_path=file_model.file_path,
            file_hash=file_model.file_hash,
            file_size=file_model.file_size,
            mime_type=file_model.mime_type,
            is_encrypted=file_model.is_encrypted,
            encryption_algorithm=file_model.encryption_algorithm,
            is_sensitive=file_model.is_sensitive,
            sensitivity_level=file_model.sensitivity_level,
            classification=file_model.classification,
            status=file_model.status,
            created_at=file_model.created_at,
            updated_at=file_model.updated_at,
            last_accessed=file_model.last_accessed
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {e}"
        )


@router.post("/encrypt", response_model=EncryptionResponse)
async def encrypt_file(
    encryption_request: EncryptionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> EncryptionResponse:
    """파일 암호화"""
    
    try:
        # 파일 조회
        file = db.query(FileModel).filter(FileModel.id == encryption_request.file_id).first()
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # 이미 암호화된 파일인지 확인
        if file.is_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is already encrypted"
            )
        
        # 암호화 엔진 가져오기
        crypto_engine = get_crypto_engine()
        
        # 암호화 키 생성
        key_id = f"encrypt_{file.file_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        key_info = crypto_engine.create_key(key_id, "AES256GCM")
        
        # 암호화된 파일 경로
        encrypted_path = f"{file.file_path}.encrypted"
        
        # 파일 암호화
        encrypt_result = crypto_engine.encrypt_file(
            file.file_path,
            encrypted_path,
            key_id
        )
        
        if not encrypt_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Encryption failed: {encrypt_result.get('error_message')}"
            )
        
        # 파일 정보 업데이트
        file.is_encrypted = True
        file.encryption_algorithm = "AES256GCM"
        file.encryption_key_id = key_id
        file.encrypted_file_path = encrypted_path
        file.updated_at = datetime.utcnow()
        
        db.commit()
        
        # 접근 로그 기록
        access_log = FileAccessLog(
            access_type="encrypt",
            access_result="success",
            file_id=file.id,
            user_id=current_user.id
        )
        db.add(access_log)
        db.commit()
        
        return EncryptionResponse(
            success=True,
            encrypted_file_path=encrypted_path,
            key_id=key_id,
            algorithm="AES256GCM",
            encryption_time_ms=encrypt_result.get("encryption_time_ms", 0),
            message="File encrypted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encrypt file: {e}"
        )


@router.post("/decrypt", response_model=EncryptionResponse)
async def decrypt_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> EncryptionResponse:
    """파일 복호화"""
    
    try:
        # 파일 조회
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # 암호화된 파일인지 확인
        if not file.is_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not encrypted"
            )
        
        # 암호화 엔진 가져오기
        crypto_engine = get_crypto_engine()
        
        # 복호화된 파일 경로
        decrypted_path = file.file_path.replace(".encrypted", ".decrypted")
        
        # 파일 복호화
        decrypt_result = crypto_engine.decrypt_file(
            file.encrypted_file_path,
            decrypted_path,
            file.encryption_key_id
        )
        
        if not decrypt_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Decryption failed: {decrypt_result.get('error_message')}"
            )
        
        # 접근 로그 기록
        access_log = FileAccessLog(
            access_type="decrypt",
            access_result="success",
            file_id=file.id,
            user_id=current_user.id
        )
        db.add(access_log)
        db.commit()
        
        return EncryptionResponse(
            success=True,
            encrypted_file_path=decrypted_path,
            key_id=file.encryption_key_id,
            algorithm=file.encryption_algorithm,
            encryption_time_ms=decrypt_result.get("decryption_time_ms", 0),
            message="File decrypted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decrypt file: {e}"
        )


@router.get("/{file_id}/access-logs", response_model=List[FileAccessLogResponse])
async def get_file_access_logs(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[FileAccessLogResponse]:
    """파일 접근 로그 조회"""
    
    # 파일 존재 확인
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # 접근 로그 조회
    access_logs = db.query(FileAccessLog).filter(FileAccessLog.file_id == file_id).all()
    
    return [
        FileAccessLogResponse(
            id=log.id,
            access_type=log.access_type,
            access_result=log.access_result,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            accessed_at=log.accessed_at
        )
        for log in access_logs
    ]


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """파일 삭제"""
    
    try:
        # 파일 조회
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # 파일 삭제 (물리적 파일)
        try:
            if os.path.exists(file.file_path):
                os.remove(file.file_path)
            if file.encrypted_file_path and os.path.exists(file.encrypted_file_path):
                os.remove(file.encrypted_file_path)
        except Exception as e:
            logging.warning(f"Failed to delete physical file: {e}")
        
        # 데이터베이스에서 파일 정보 삭제
        db.delete(file)
        db.commit()
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {e}"
        )


async def analyze_uploaded_file(file_path: str, file_hash: str):
    """업로드된 파일 위협 분석 (백그라운드 작업)"""
    try:
        from app.services.rl_agent import threat_analyzer
        
        # 위협 분석 실행
        analysis_result = threat_analyzer.analyze_file(file_path, file_hash)
        
        if analysis_result.get("threat_detected", False):
            logging.warning(f"Threat detected in uploaded file: {file_path}")
            logging.warning(f"Analysis result: {analysis_result}")
            
            # TODO: 데이터베이스에 위협 정보 저장
            # TODO: 관리자에게 알림 전송
        
    except Exception as e:
        logging.error(f"Failed to analyze uploaded file {file_path}: {e}")