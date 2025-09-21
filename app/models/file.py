"""
File management and encryption models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class File(Base):
    """파일 모델"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(100), unique=True, index=True, nullable=False)
    original_name = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    
    # 암호화 정보
    is_encrypted = Column(Boolean, default=False)
    encryption_algorithm = Column(String(50))
    encryption_key_id = Column(String(100))
    encrypted_file_path = Column(Text)
    
    # 보안 정보
    is_sensitive = Column(Boolean, default=False)
    sensitivity_level = Column(String(20))  # public, internal, confidential, restricted
    classification = Column(String(50))  # medical, financial, personal, etc.
    
    # 상태 정보
    status = Column(String(20), default="active")  # active, archived, deleted
    is_monitored = Column(Boolean, default=True)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True))
    
    # 관계
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="files")
    access_logs = relationship("FileAccessLog", back_populates="file")
    
    def __repr__(self):
        return f"<File(id={self.id}, file_id='{self.file_id}', name='{self.original_name}')>"


class FileAccessLog(Base):
    """파일 접근 로그 모델"""
    __tablename__ = "file_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    access_type = Column(String(50), nullable=False)  # read, write, delete, encrypt, decrypt
    access_result = Column(String(20), nullable=False)  # success, failed, denied
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # 접근 정보
    file_id = Column(Integer, ForeignKey("files.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 타임스탬프
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    file = relationship("File", back_populates="access_logs")
    user = relationship("User", back_populates="file_access_logs")
    
    def __repr__(self):
        return f"<FileAccessLog(id={self.id}, type='{self.access_type}', result='{self.access_result}')>"


class EncryptionKey(Base):
    """암호화 키 모델"""
    __tablename__ = "encryption_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(100), unique=True, index=True, nullable=False)
    key_type = Column(String(50), nullable=False)  # AES, RSA, etc.
    key_size = Column(Integer, nullable=False)  # 256, 2048, etc.
    key_data = Column(Text, nullable=False)  # 암호화된 키 데이터
    is_active = Column(Boolean, default=True)
    
    # 키 정보
    created_by = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime(timezone=True))
    rotation_count = Column(Integer, default=0)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<EncryptionKey(id={self.id}, key_id='{self.key_id}', type='{self.key_type}')>"