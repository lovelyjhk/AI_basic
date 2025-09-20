"""
Audit logging models for compliance and security
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """감사 로그 모델"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    event_category = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # info, warning, error, critical
    
    # 이벤트 정보
    description = Column(Text, nullable=False)
    source_ip = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(100))
    
    # 데이터 정보
    affected_resource = Column(String(200))
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    # 결과 정보
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    
    # 타임스탬프
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, type='{self.event_type}', severity='{self.severity}')>"


class LoginAttempt(Base):
    """로그인 시도 모델"""
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(200))
    
    # 보안 정보
    is_suspicious = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)  # 0-100
    
    # 타임스탬프
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="login_attempts")
    
    def __repr__(self):
        return f"<LoginAttempt(id={self.id}, email='{self.email}', success={self.success})>"


class SystemLog(Base):
    """시스템 로그 모델"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_level = Column(String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    component = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    
    # 추가 정보
    exception_info = Column(Text)
    stack_trace = Column(Text)
    context_data = Column(JSON)
    
    # 타임스탬프
    logged_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level='{self.log_level}', component='{self.component}')>"


class ComplianceLog(Base):
    """규정 준수 로그 모델"""
    __tablename__ = "compliance_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    regulation = Column(String(100), nullable=False)  # HIPAA, GDPR, FDA, etc.
    requirement = Column(String(200), nullable=False)
    compliance_status = Column(String(20), nullable=False)  # compliant, non_compliant, pending
    
    # 준수 정보
    evidence = Column(Text)
    remediation_actions = Column(Text)
    next_review_date = Column(DateTime(timezone=True))
    
    # 타임스탬프
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ComplianceLog(id={self.id}, regulation='{self.regulation}', status='{self.compliance_status}')>"