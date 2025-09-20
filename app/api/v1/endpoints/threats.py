"""
Threat detection and analysis endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.threat import Threat, ThreatPattern, SecurityEvent
from app.schemas.threat import (
    ThreatResponse, 
    ThreatCreate, 
    ThreatUpdate,
    ThreatAnalysisRequest,
    ThreatAnalysisResponse
)

router = APIRouter()


@router.get("/", response_model=List[ThreatResponse])
async def get_threats(
    skip: int = 0,
    limit: int = 100,
    threat_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[ThreatResponse]:
    """탐지된 위협 목록 조회"""
    
    query = db.query(Threat)
    
    # 필터링
    if threat_type:
        query = query.filter(Threat.threat_type == threat_type)
    if severity:
        query = query.filter(Threat.severity == severity)
    if status:
        query = query.filter(Threat.status == status)
    
    threats = query.offset(skip).limit(limit).all()
    
    return [
        ThreatResponse(
            id=threat.id,
            threat_id=threat.threat_id,
            threat_type=threat.threat_type,
            severity=threat.severity,
            confidence_score=threat.confidence_score,
            status=threat.status,
            source_ip=threat.source_ip,
            target_ip=threat.target_ip,
            file_path=threat.file_path,
            description=threat.description,
            detected_at=threat.detected_at,
            analyzed_at=threat.analyzed_at,
            resolved_at=threat.resolved_at
        )
        for threat in threats
    ]


@router.get("/{threat_id}", response_model=ThreatResponse)
async def get_threat(
    threat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ThreatResponse:
    """특정 위협 상세 정보 조회"""
    
    threat = db.query(Threat).filter(Threat.id == threat_id).first()
    if not threat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found"
        )
    
    return ThreatResponse(
        id=threat.id,
        threat_id=threat.threat_id,
        threat_type=threat.threat_type,
        severity=threat.severity,
        confidence_score=threat.confidence_score,
        status=threat.status,
        source_ip=threat.source_ip,
        target_ip=threat.target_ip,
        file_path=threat.file_path,
        description=threat.description,
        detected_at=threat.detected_at,
        analyzed_at=threat.analyzed_at,
        resolved_at=threat.resolved_at
    )


@router.post("/analyze", response_model=ThreatAnalysisResponse)
async def analyze_threat(
    analysis_request: ThreatAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ThreatAnalysisResponse:
    """파일 위협 분석"""
    
    # TODO: 실제 RL 에이전트를 통한 위협 분석 구현
    from app.services.rl_agent import ThreatAnalyzer
    
    analyzer = ThreatAnalyzer()
    
    # 백그라운드에서 분석 실행
    background_tasks.add_task(
        analyzer.analyze_file,
        analysis_request.file_path,
        analysis_request.file_hash
    )
    
    # 임시 응답 (실제로는 분석 결과를 반환)
    return ThreatAnalysisResponse(
        threat_detected=True,
        confidence_score=0.85,
        threat_type="malware",
        severity="high",
        analysis_result={
            "suspicious_patterns": ["encrypted_payload", "obfuscated_code"],
            "behavioral_indicators": ["file_modification", "network_communication"],
            "recommended_actions": ["quarantine", "deep_scan", "user_notification"]
        }
    )


@router.put("/{threat_id}", response_model=ThreatResponse)
async def update_threat(
    threat_id: int,
    threat_update: ThreatUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ThreatResponse:
    """위협 정보 업데이트"""
    
    threat = db.query(Threat).filter(Threat.id == threat_id).first()
    if not threat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found"
        )
    
    # 업데이트할 필드들
    update_data = threat_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(threat, field, value)
    
    # 상태가 변경된 경우 타임스탬프 업데이트
    if threat_update.status:
        if threat_update.status == "analyzed":
            threat.analyzed_at = datetime.utcnow()
        elif threat_update.status == "resolved":
            threat.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(threat)
    
    return ThreatResponse(
        id=threat.id,
        threat_id=threat.threat_id,
        threat_type=threat.threat_type,
        severity=threat.severity,
        confidence_score=threat.confidence_score,
        status=threat.status,
        source_ip=threat.source_ip,
        target_ip=threat.target_ip,
        file_path=threat.file_path,
        description=threat.description,
        detected_at=threat.detected_at,
        analyzed_at=threat.analyzed_at,
        resolved_at=threat.resolved_at
    )


@router.delete("/{threat_id}")
async def delete_threat(
    threat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """위협 삭제 (관리자만)"""
    
    # 관리자 권한 확인
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    threat = db.query(Threat).filter(Threat.id == threat_id).first()
    if not threat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found"
        )
    
    db.delete(threat)
    db.commit()
    
    return {"message": "Threat deleted successfully"}


@router.get("/patterns/", response_model=List[dict])
async def get_threat_patterns(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """위협 패턴 목록 조회"""
    
    patterns = db.query(ThreatPattern).filter(ThreatPattern.is_active == True).all()
    
    return [
        {
            "id": pattern.id,
            "pattern_name": pattern.pattern_name,
            "pattern_type": pattern.pattern_type,
            "description": pattern.description,
            "detection_count": pattern.detection_count,
            "accuracy": pattern.accuracy
        }
        for pattern in patterns
    ]


@router.get("/statistics/", response_model=dict)
async def get_threat_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """위협 통계 조회"""
    
    from sqlalchemy import func
    
    # 전체 위협 수
    total_threats = db.query(func.count(Threat.id)).scalar()
    
    # 심각도별 통계
    severity_stats = db.query(
        Threat.severity,
        func.count(Threat.id)
    ).group_by(Threat.severity).all()
    
    # 타입별 통계
    type_stats = db.query(
        Threat.threat_type,
        func.count(Threat.id)
    ).group_by(Threat.threat_type).all()
    
    # 상태별 통계
    status_stats = db.query(
        Threat.status,
        func.count(Threat.id)
    ).group_by(Threat.status).all()
    
    return {
        "total_threats": total_threats,
        "severity_distribution": dict(severity_stats),
        "type_distribution": dict(type_stats),
        "status_distribution": dict(status_stats)
    }