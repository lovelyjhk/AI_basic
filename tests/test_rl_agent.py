"""
RL Agent tests
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import os

from app.services.rl_agent import CybersecurityEnv, ThreatAnalyzer


def test_cybersecurity_env():
    """사이버보안 환경 테스트"""
    env = CybersecurityEnv()
    
    # 환경 초기화
    obs, info = env.reset()
    assert obs.shape == (6,)
    assert isinstance(obs, np.ndarray)
    
    # 액션 실행
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    
    assert obs.shape == (6,)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert "action" in info


def test_threat_analyzer_heuristic():
    """위협 분석기 휴리스틱 테스트"""
    analyzer = ThreatAnalyzer()
    
    # 테스트 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, Medical Cybersecurity System!")
        test_file = f.name
    
    try:
        # 파일 분석
        result = analyzer.analyze_file(test_file)
        
        assert "threat_detected" in result
        assert "confidence" in result
        assert "threat_level" in result
        assert "analysis_method" in result
        
        # 휴리스틱 분석 결과 확인
        assert result["analysis_method"] == "heuristic"
        
    finally:
        # 정리
        os.unlink(test_file)


def test_threat_analyzer_suspicious_file():
    """의심스러운 파일 분석 테스트"""
    analyzer = ThreatAnalyzer()
    
    # 의심스러운 내용이 포함된 테스트 파일 생성
    suspicious_content = """
    <script>alert('XSS')</script>
    eval('malicious_code')
    powershell -Command "Get-Process"
    """
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
        f.write(suspicious_content)
        test_file = f.name
    
    try:
        # 파일 분석
        result = analyzer.analyze_file(test_file)
        
        # 의심스러운 패턴이 감지되어야 함
        assert result["threat_detected"] is True
        assert result["confidence"] > 0.3
        assert result["threat_level"] in ["low", "medium", "high"]
        
    finally:
        # 정리
        os.unlink(test_file)


def test_threat_analyzer_large_file():
    """대용량 파일 분석 테스트"""
    analyzer = ThreatAnalyzer()
    
    # 대용량 테스트 파일 생성 (10MB)
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
        # 1MB씩 10번 쓰기
        for _ in range(10):
            f.write(b'0' * 1024 * 1024)
        test_file = f.name
    
    try:
        # 파일 분석
        result = analyzer.analyze_file(test_file)
        
        # 대용량 파일 특성 확인
        assert "threat_detected" in result
        assert result["analysis_method"] == "heuristic"
        
    finally:
        # 정리
        os.unlink(test_file)


def test_threat_analyzer_encrypted_file():
    """암호화된 파일 분석 테스트"""
    analyzer = ThreatAnalyzer()
    
    # 고엔트로피 데이터 생성 (암호화된 파일 시뮬레이션)
    import secrets
    encrypted_data = secrets.token_bytes(1024 * 10)  # 10KB 랜덤 데이터
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.enc') as f:
        f.write(encrypted_data)
        test_file = f.name
    
    try:
        # 파일 분석
        result = analyzer.analyze_file(test_file)
        
        # 고엔트로피 파일 특성 확인
        assert "threat_detected" in result
        assert result["analysis_method"] == "heuristic"
        
    finally:
        # 정리
        os.unlink(test_file)


def test_cybersecurity_env_multiple_steps():
    """사이버보안 환경 다중 스텝 테스트"""
    env = CybersecurityEnv()
    
    obs, info = env.reset()
    
    # 여러 스텝 실행
    for _ in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        
        assert obs.shape == (6,)
        assert isinstance(reward, float)
        
        if terminated or truncated:
            break
    
    # 환경 재설정
    obs, info = env.reset()
    assert obs.shape == (6,)


def test_threat_analyzer_file_hash():
    """파일 해시 계산 테스트"""
    analyzer = ThreatAnalyzer()
    
    # 테스트 파일 생성
    test_content = "Test content for hash calculation"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(test_content)
        test_file = f.name
    
    try:
        # 파일 해시 계산
        file_hash = analyzer._calculate_file_hash(test_file)
        
        assert isinstance(file_hash, str)
        assert len(file_hash) == 64  # SHA-256 해시 길이
        
    finally:
        # 정리
        os.unlink(test_file)


def test_threat_analyzer_file_features():
    """파일 특성 추출 테스트"""
    analyzer = ThreatAnalyzer()
    
    # 테스트 파일 생성
    test_content = "Test content for feature extraction"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(test_content)
        test_file = f.name
    
    try:
        # 파일 특성 추출
        features = analyzer._extract_file_features(test_file)
        
        assert "file_size" in features
        assert "file_extension" in features
        assert "file_hash" in features
        assert "entropy" in features
        assert "suspicious_patterns" in features
        
        assert features["file_size"] > 0
        assert features["file_extension"] == ".txt"
        assert len(features["file_hash"]) == 64
        
    finally:
        # 정리
        os.unlink(test_file)