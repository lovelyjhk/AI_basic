"""
Cryptographic engine tests
"""

import pytest
import tempfile
import os
from pathlib import Path

from app.services.crypto_engine import CryptoEngine, get_crypto_engine


def test_crypto_engine_initialization():
    """암호화 엔진 초기화 테스트"""
    engine = CryptoEngine("test_master_key_32_chars_long!")
    
    assert engine.master_key == "test_master_key_32_chars_long!"
    assert engine.lib is not None


def test_create_encryption_key():
    """암호화 키 생성 테스트"""
    engine = CryptoEngine("test_master_key_32_chars_long!")
    
    key_info = engine.create_key("test_key_001", "AES256GCM")
    
    assert key_info["key_id"] == "test_key_001"
    assert key_info["algorithm"] == "AES256GCM"
    assert key_info["key_size"] == 32
    assert key_info["is_active"] is True


def test_encrypt_decrypt_file():
    """파일 암호화/복호화 테스트"""
    engine = CryptoEngine("test_master_key_32_chars_long!")
    
    # 테스트 파일 생성
    test_content = "Hello, Medical Cybersecurity System!"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(test_content)
        input_file = f.name
    
    encrypted_file = input_file + ".encrypted"
    decrypted_file = input_file + ".decrypted"
    
    try:
        # 키 생성
        key_info = engine.create_key("test_key_002", "AES256GCM")
        
        # 파일 암호화
        encrypt_result = engine.encrypt_file(input_file, encrypted_file, "test_key_002")
        
        assert encrypt_result["success"] is True
        assert encrypt_result["encrypted_file_path"] == encrypted_file
        assert encrypt_result["key_id"] == "test_key_002"
        
        # 암호화된 파일 존재 확인
        assert os.path.exists(encrypted_file)
        
        # 파일 복호화
        decrypt_result = engine.decrypt_file(encrypted_file, decrypted_file, "test_key_002")
        
        assert decrypt_result["success"] is True
        assert decrypt_result["decrypted_file_path"] == decrypted_file
        
        # 복호화된 파일 존재 확인
        assert os.path.exists(decrypted_file)
        
        # 원본과 복호화된 파일 내용 비교
        with open(input_file, 'r') as f1, open(decrypted_file, 'r') as f2:
            original = f1.read()
            decrypted = f2.read()
            assert original == decrypted
        
    finally:
        # 정리
        for file_path in [input_file, encrypted_file, decrypted_file]:
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass


def test_encrypt_nonexistent_file():
    """존재하지 않는 파일 암호화 테스트"""
    engine = CryptoEngine("test_master_key_32_chars_long!")
    
    # 키 생성
    key_info = engine.create_key("test_key_003", "AES256GCM")
    
    # 존재하지 않는 파일 암호화 시도
    encrypt_result = engine.encrypt_file(
        "/nonexistent/file.txt",
        "/nonexistent/encrypted.bin",
        "test_key_003"
    )
    
    assert encrypt_result["success"] is False
    assert encrypt_result["error_message"] is not None


def test_decrypt_with_wrong_key():
    """잘못된 키로 복호화 테스트"""
    engine = CryptoEngine("test_master_key_32_chars_long!")
    
    # 테스트 파일 생성
    test_content = "Test content for wrong key decryption"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(test_content)
        input_file = f.name
    
    encrypted_file = input_file + ".encrypted"
    decrypted_file = input_file + ".decrypted"
    
    try:
        # 올바른 키로 암호화
        key_info1 = engine.create_key("correct_key", "AES256GCM")
        encrypt_result = engine.encrypt_file(input_file, encrypted_file, "correct_key")
        assert encrypt_result["success"] is True
        
        # 잘못된 키로 복호화 시도
        key_info2 = engine.create_key("wrong_key", "AES256GCM")
        decrypt_result = engine.decrypt_file(encrypted_file, decrypted_file, "wrong_key")
        
        # 복호화 실패 예상
        assert decrypt_result["success"] is False
        assert decrypt_result["error_message"] is not None
        
    finally:
        # 정리
        for file_path in [input_file, encrypted_file, decrypted_file]:
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass


def test_file_hash_calculation():
    """파일 해시 계산 테스트"""
    engine = CryptoEngine("test_master_key_32_chars_long!")
    
    # 테스트 파일 생성
    test_content = "Test content for hash calculation"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(test_content)
        test_file = f.name
    
    try:
        # 파일 해시 계산
        file_hash = engine._calculate_file_hash(test_file)
        
        assert isinstance(file_hash, str)
        assert len(file_hash) == 64  # SHA-256 해시 길이
        
        # 동일한 내용의 파일은 동일한 해시를 가져야 함
        file_hash2 = engine._calculate_file_hash(test_file)
        assert file_hash == file_hash2
        
    finally:
        # 정리
        os.unlink(test_file)


def test_get_crypto_engine_singleton():
    """암호화 엔진 싱글톤 테스트"""
    engine1 = get_crypto_engine()
    engine2 = get_crypto_engine()
    
    # 동일한 인스턴스여야 함
    assert engine1 is engine2


def test_encrypt_large_file():
    """대용량 파일 암호화 테스트"""
    engine = CryptoEngine("test_master_key_32_chars_long!")
    
    # 대용량 테스트 파일 생성 (1MB)
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
        f.write(b'0' * 1024 * 1024)  # 1MB
        input_file = f.name
    
    encrypted_file = input_file + ".encrypted"
    decrypted_file = input_file + ".decrypted"
    
    try:
        # 키 생성
        key_info = engine.create_key("large_file_key", "AES256GCM")
        
        # 파일 암호화
        encrypt_result = engine.encrypt_file(input_file, encrypted_file, "large_file_key")
        
        assert encrypt_result["success"] is True
        assert os.path.exists(encrypted_file)
        
        # 파일 복호화
        decrypt_result = engine.decrypt_file(encrypted_file, decrypted_file, "large_file_key")
        
        assert decrypt_result["success"] is True
        assert os.path.exists(decrypted_file)
        
        # 파일 크기 확인
        original_size = os.path.getsize(input_file)
        decrypted_size = os.path.getsize(decrypted_file)
        assert original_size == decrypted_size
        
    finally:
        # 정리
        for file_path in [input_file, encrypted_file, decrypted_file]:
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass


def test_key_management():
    """키 관리 테스트"""
    engine = CryptoEngine("test_master_key_32_chars_long!")
    
    # 키 생성
    key_info = engine.create_key("management_test_key", "AES256GCM")
    assert key_info["key_id"] == "management_test_key"
    
    # 키 정보 조회
    retrieved_key_info = engine.get_key_info("management_test_key")
    assert retrieved_key_info["key_id"] == "management_test_key"
    assert retrieved_key_info["algorithm"] == "AES256GCM"
    
    # 키 삭제
    delete_result = engine.delete_key("management_test_key")
    assert delete_result is True