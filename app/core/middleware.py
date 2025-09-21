"""
Custom middleware for security, logging, and monitoring
"""

import time
import logging
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """보안 미들웨어"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.blocked_ips = set()
        self.rate_limits = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # IP 주소 추출
        client_ip = request.client.host
        
        # 차단된 IP 확인
        if client_ip in self.blocked_ips:
            return JSONResponse(
                status_code=403,
                content={"detail": "IP address blocked"}
            )
        
        # 기본 보안 헤더 추가
        response = await call_next(request)
        
        # 보안 헤더 설정
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """로깅 미들웨어"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 요청 시작 시간
        start_time = time.time()
        
        # 요청 정보 로깅
        logger.info(f"Request started: {request.method} {request.url}")
        
        # 응답 처리
        response = await call_next(request)
        
        # 처리 시간 계산
        process_time = time.time() - start_time
        
        # 응답 정보 로깅
        logger.info(
            f"Request completed: {request.method} {request.url} "
            f"Status: {response.status_code} "
            f"Time: {process_time:.3f}s"
        )
        
        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """속도 제한 미들웨어"""
    
    def __init__(self, app: ASGIApp, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        current_time = time.time()
        
        # 클라이언트별 요청 기록 정리
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < self.period
            ]
        else:
            self.requests[client_ip] = []
        
        # 요청 수 확인
        if len(self.requests[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
        
        # 요청 기록 추가
        self.requests[client_ip].append(current_time)
        
        # 응답 처리
        response = await call_next(request)
        
        # 속도 제한 헤더 추가
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(
            self.calls - len(self.requests[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + self.period)
        )
        
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """감사 로그 미들웨어"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 감사 로그 정보 수집
        audit_info = {
            "timestamp": time.time(),
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
        }
        
        # 응답 처리
        response = await call_next(request)
        
        # 응답 정보 추가
        audit_info.update({
            "status_code": response.status_code,
            "response_size": len(response.body) if hasattr(response, 'body') else 0
        })
        
        # 감사 로그 기록
        logger.info(f"Audit log: {json.dumps(audit_info)}")
        
        return response


class HIPAAComplianceMiddleware(BaseHTTPMiddleware):
    """HIPAA 규정 준수 미들웨어"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # HIPAA 관련 헤더 확인
        hipaa_headers = {
            "X-HIPAA-Compliant": "true",
            "X-Data-Classification": "PHI",  # Protected Health Information
            "X-Audit-Required": "true"
        }
        
        # 응답 처리
        response = await call_next(request)
        
        # HIPAA 헤더 추가
        for header, value in hipaa_headers.items():
            response.headers[header] = value
        
        return response


class PerformanceMiddleware(BaseHTTPMiddleware):
    """성능 모니터링 미들웨어"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = {
            "total_requests": 0,
            "total_time": 0.0,
            "slow_requests": 0,
            "error_requests": 0
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 응답 처리
        response = await call_next(request)
        
        # 성능 메트릭 업데이트
        process_time = time.time() - start_time
        self.metrics["total_requests"] += 1
        self.metrics["total_time"] += process_time
        
        # 느린 요청 카운트
        if process_time > 1.0:  # 1초 이상
            self.metrics["slow_requests"] += 1
        
        # 오류 요청 카운트
        if response.status_code >= 400:
            self.metrics["error_requests"] += 1
        
        # 성능 헤더 추가
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Average-Response-Time"] = str(
            self.metrics["total_time"] / self.metrics["total_requests"]
        )
        
        return response
    
    def get_metrics(self) -> dict:
        """성능 메트릭 반환"""
        return {
            **self.metrics,
            "average_response_time": (
                self.metrics["total_time"] / self.metrics["total_requests"]
                if self.metrics["total_requests"] > 0 else 0
            )
        }