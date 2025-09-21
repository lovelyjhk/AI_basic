"""
Custom exception handlers
"""

import logging
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class MedicalCybersecurityException(Exception):
    """기본 예외 클래스"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ThreatDetectionError(MedicalCybersecurityException):
    """위협 탐지 오류"""
    pass


class EncryptionError(MedicalCybersecurityException):
    """암호화 오류"""
    pass


class FileProcessingError(MedicalCybersecurityException):
    """파일 처리 오류"""
    pass


class AuthenticationError(MedicalCybersecurityException):
    """인증 오류"""
    pass


class AuthorizationError(MedicalCybersecurityException):
    """권한 오류"""
    pass


class HIPAAComplianceError(MedicalCybersecurityException):
    """HIPAA 규정 준수 오류"""
    pass


def setup_exception_handlers(app: FastAPI):
    """예외 핸들러 설정"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP 예외 핸들러"""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """Starlette HTTP 예외 핸들러"""
        logger.warning(f"Starlette HTTP exception: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """요청 검증 오류 핸들러"""
        logger.warning(f"Validation error: {exc.errors()}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Invalid request data",
                "details": exc.errors(),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """데이터베이스 오류 핸들러"""
        logger.error(f"Database error: {str(exc)}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Database Error",
                "message": "Internal database error",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(ThreatDetectionError)
    async def threat_detection_exception_handler(request: Request, exc: ThreatDetectionError):
        """위협 탐지 오류 핸들러"""
        logger.error(f"Threat detection error: {exc.message}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Threat Detection Error",
                "message": exc.message,
                "error_code": exc.error_code,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(EncryptionError)
    async def encryption_exception_handler(request: Request, exc: EncryptionError):
        """암호화 오류 핸들러"""
        logger.error(f"Encryption error: {exc.message}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Encryption Error",
                "message": exc.message,
                "error_code": exc.error_code,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(FileProcessingError)
    async def file_processing_exception_handler(request: Request, exc: FileProcessingError):
        """파일 처리 오류 핸들러"""
        logger.error(f"File processing error: {exc.message}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "File Processing Error",
                "message": exc.message,
                "error_code": exc.error_code,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(AuthenticationError)
    async def authentication_exception_handler(request: Request, exc: AuthenticationError):
        """인증 오류 핸들러"""
        logger.warning(f"Authentication error: {exc.message}")
        
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication Error",
                "message": exc.message,
                "error_code": exc.error_code,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(AuthorizationError)
    async def authorization_exception_handler(request: Request, exc: AuthorizationError):
        """권한 오류 핸들러"""
        logger.warning(f"Authorization error: {exc.message}")
        
        return JSONResponse(
            status_code=403,
            content={
                "error": "Authorization Error",
                "message": exc.message,
                "error_code": exc.error_code,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(HIPAAComplianceError)
    async def hipaa_compliance_exception_handler(request: Request, exc: HIPAAComplianceError):
        """HIPAA 규정 준수 오류 핸들러"""
        logger.error(f"HIPAA compliance error: {exc.message}")
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "HIPAA Compliance Error",
                "message": exc.message,
                "error_code": exc.error_code,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """Pydantic 검증 오류 핸들러"""
        logger.warning(f"Pydantic validation error: {exc.errors()}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Invalid data format",
                "details": exc.errors(),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """일반 예외 핸들러"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


def raise_threat_detection_error(message: str, error_code: str = None):
    """위협 탐지 오류 발생"""
    raise ThreatDetectionError(message, error_code)


def raise_encryption_error(message: str, error_code: str = None):
    """암호화 오류 발생"""
    raise EncryptionError(message, error_code)


def raise_file_processing_error(message: str, error_code: str = None):
    """파일 처리 오류 발생"""
    raise FileProcessingError(message, error_code)


def raise_authentication_error(message: str, error_code: str = None):
    """인증 오류 발생"""
    raise AuthenticationError(message, error_code)


def raise_authorization_error(message: str, error_code: str = None):
    """권한 오류 발생"""
    raise AuthorizationError(message, error_code)


def raise_hipaa_compliance_error(message: str, error_code: str = None):
    """HIPAA 규정 준수 오류 발생"""
    raise HIPAAComplianceError(message, error_code)