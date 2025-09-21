"""
File management schemas
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileBase(BaseModel):
    """파일 기본 스키마"""
    original_name: str
    file_path: str
    file_hash: str
    file_size: int
    mime_type: Optional[str] = None
    is_sensitive: bool = False
    sensitivity_level: str = "internal"
    classification: str = "general"


class FileCreate(FileBase):
    """파일 생성 스키마"""
    pass


class FileUpdate(BaseModel):
    """파일 업데이트 스키마"""
    is_sensitive: Optional[bool] = None
    sensitivity_level: Optional[str] = None
    classification: Optional[str] = None
    status: Optional[str] = None


class FileResponse(FileBase):
    """파일 응답 스키마"""
    id: int
    file_id: str
    is_encrypted: bool
    encryption_algorithm: Optional[str] = None
    encryption_key_id: Optional[str] = None
    encrypted_file_path: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EncryptionRequest(BaseModel):
    """암호화 요청 스키마"""
    file_id: int
    algorithm: str = "AES256GCM"


class EncryptionResponse(BaseModel):
    """암호화 응답 스키마"""
    success: bool
    encrypted_file_path: Optional[str] = None
    key_id: Optional[str] = None
    algorithm: Optional[str] = None
    encryption_time_ms: int = 0
    message: str


class DecryptionRequest(BaseModel):
    """복호화 요청 스키마"""
    file_id: int


class DecryptionResponse(BaseModel):
    """복호화 응답 스키마"""
    success: bool
    decrypted_file_path: Optional[str] = None
    decryption_time_ms: int = 0
    message: str


class FileAccessLogBase(BaseModel):
    """파일 접근 로그 기본 스키마"""
    access_type: str
    access_result: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class FileAccessLogResponse(FileAccessLogBase):
    """파일 접근 로그 응답 스키마"""
    id: int
    accessed_at: datetime
    
    class Config:
        from_attributes = True


class FileStatistics(BaseModel):
    """파일 통계 스키마"""
    total_files: int
    encrypted_files: int
    sensitive_files: int
    total_size: int
    average_size: float
    files_by_classification: dict
    files_by_sensitivity: dict