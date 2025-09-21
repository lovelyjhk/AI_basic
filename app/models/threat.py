"""
Threat detection and analysis models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Threat(Base):
    """위협 탐지 모델"""
    __tablename__ = "threats"
    
    id = Column(Integer, primary_key=True, index=True)
    threat_id = Column(String(100), unique=True, index=True, nullable=False)
    threat_type = Column(String(100), nullable=False)  # malware, phishing, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    confidence_score = Column(Float, nullable=False)  # 0.0 - 1.0
    status = Column(String(20), default="detected")  # detected, analyzed, resolved, false_positive
    
    # 위협 정보
    source_ip = Column(String(45))  # IPv4/IPv6
    target_ip = Column(String(45))
    file_path = Column(Text)
    file_hash = Column(String(64))  # SHA-256
    description = Column(Text)
    
    # 분석 결과
    analysis_result = Column(JSON)
    mitigation_actions = Column(JSON)
    false_positive = Column(Boolean, default=False)
    
    # 타임스탬프
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    analyzed_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # 관계
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="threats")
    
    def __repr__(self):
        return f"<Threat(id={self.id}, threat_id='{self.threat_id}', type='{self.threat_type}')>"


class ThreatPattern(Base):
    """위협 패턴 모델"""
    __tablename__ = "threat_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String(200), nullable=False)
    pattern_type = Column(String(100), nullable=False)  # signature, behavioral, etc.
    pattern_data = Column(JSON, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # 통계
    detection_count = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ThreatPattern(id={self.id}, name='{self.pattern_name}')>"


class SecurityEvent(Base):
    """보안 이벤트 모델"""
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    event_category = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    
    # 이벤트 정보
    source = Column(String(200))
    target = Column(String(200))
    description = Column(Text)
    event_data = Column(JSON)
    
    # 처리 정보
    is_processed = Column(Boolean, default=False)
    processing_notes = Column(Text)
    
    # 타임스탬프
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, type='{self.event_type}')>"