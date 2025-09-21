"""
Threat detection schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ThreatBase(BaseModel):
    """위협 기본 스키마"""
    threat_type: str
    severity: str
    confidence_score: float
    source_ip: Optional[str] = None
    target_ip: Optional[str] = None
    file_path: Optional[str] = None
    description: Optional[str] = None


class ThreatCreate(ThreatBase):
    """위협 생성 스키마"""
    threat_id: str
    file_hash: Optional[str] = None


class ThreatUpdate(BaseModel):
    """위협 업데이트 스키마"""
    status: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None
    mitigation_actions: Optional[Dict[str, Any]] = None
    false_positive: Optional[bool] = None


class ThreatResponse(ThreatBase):
    """위협 응답 스키마"""
    id: int
    threat_id: str
    status: str
    detected_at: datetime
    analyzed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ThreatAnalysisRequest(BaseModel):
    """위협 분석 요청 스키마"""
    file_path: str
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class ThreatAnalysisResponse(BaseModel):
    """위협 분석 응답 스키마"""
    threat_detected: bool
    confidence_score: float
    threat_type: Optional[str] = None
    severity: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None


class ThreatPatternBase(BaseModel):
    """위협 패턴 기본 스키마"""
    pattern_name: str
    pattern_type: str
    description: Optional[str] = None


class ThreatPatternCreate(ThreatPatternBase):
    """위협 패턴 생성 스키마"""
    pattern_data: Dict[str, Any]


class ThreatPatternUpdate(BaseModel):
    """위협 패턴 업데이트 스키마"""
    pattern_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ThreatPattern(ThreatPatternBase):
    """위협 패턴 응답 스키마"""
    id: int
    is_active: bool
    detection_count: int
    false_positive_count: int
    accuracy: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class SecurityEventBase(BaseModel):
    """보안 이벤트 기본 스키마"""
    event_type: str
    event_category: str
    severity: str
    source: Optional[str] = None
    target: Optional[str] = None
    description: Optional[str] = None


class SecurityEventCreate(SecurityEventBase):
    """보안 이벤트 생성 스키마"""
    event_data: Optional[Dict[str, Any]] = None


class SecurityEvent(SecurityEventBase):
    """보안 이벤트 응답 스키마"""
    id: int
    is_processed: bool
    processing_notes: Optional[str] = None
    occurred_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True