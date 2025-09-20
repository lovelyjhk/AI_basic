"""
API endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash

# 테스트 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_user():
    """테스트 사용자 생성"""
    db = TestingSessionLocal()
    
    # 테스트 역할 생성
    test_role = Role(
        name="test_user",
        description="Test User Role",
        permissions="read,write"
    )
    db.add(test_role)
    db.commit()
    db.refresh(test_role)
    
    # 테스트 사용자 생성
    test_user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        role_id=test_role.id
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    yield test_user
    
    # 정리
    db.delete(test_user)
    db.delete(test_role)
    db.commit()
    db.close()


@pytest.fixture
def auth_headers(test_user):
    """인증 헤더 생성"""
    # 로그인 요청
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Medical Cybersecurity System" in response.json()["message"]


def test_health_check():
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success(test_user):
    """로그인 성공 테스트"""
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_login_invalid_credentials():
    """잘못된 자격 증명으로 로그인 테스트"""
    login_data = {
        "email": "test@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 401


def test_register_user():
    """사용자 등록 테스트"""
    user_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "newpassword"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == 200
    assert response.json()["email"] == "newuser@example.com"


def test_get_current_user(auth_headers):
    """현재 사용자 정보 조회 테스트"""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_get_threats(auth_headers):
    """위협 목록 조회 테스트"""
    response = client.get("/api/v1/threats/", headers=auth_headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_files(auth_headers):
    """파일 목록 조회 테스트"""
    response = client.get("/api/v1/files/", headers=auth_headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_monitoring_statistics(auth_headers):
    """모니터링 통계 조회 테스트"""
    response = client.get("/api/v1/monitoring/statistics", headers=auth_headers)
    
    assert response.status_code == 200
    assert "monitoring" in response.json()


def test_monitoring_health():
    """모니터링 헬스 체크 테스트"""
    response = client.get("/api/v1/monitoring/health")
    
    assert response.status_code == 200
    assert "status" in response.json()


def test_unauthorized_access():
    """인증되지 않은 접근 테스트"""
    response = client.get("/api/v1/threats/")
    
    assert response.status_code == 401


def test_invalid_endpoint():
    """존재하지 않는 엔드포인트 테스트"""
    response = client.get("/api/v1/invalid")
    
    assert response.status_code == 404