"""
Python-Rust FFI Binding for Cryptographic Engine
"""

import ctypes
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CryptoEngine:
    """Rust 암호화 엔진 Python 바인딩"""
    
    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.getenv("CRYPTO_MASTER_KEY", "default_master_key_32_chars!")
        self.lib = None
        self.service = None
        self._load_library()
        self._initialize_service()
    
    def _load_library(self):
        """Rust 라이브러리 로드"""
        try:
            # Rust 라이브러리 경로
            lib_path = Path(__file__).parent.parent.parent / "rust_crypto" / "target" / "release"
            
            if sys.platform == "win32":
                lib_name = "medical_crypto.dll"
            elif sys.platform == "darwin":
                lib_name = "libmedical_crypto.dylib"
            else:
                lib_name = "libmedical_crypto.so"
            
            lib_file = lib_path / lib_name
            
            if not lib_file.exists():
                raise FileNotFoundError(f"Rust library not found: {lib_file}")
            
            # 라이브러리 로드
            self.lib = ctypes.CDLL(str(lib_file))
            self._setup_function_signatures()
            
            logger.info(f"Rust crypto library loaded: {lib_file}")
            
        except Exception as e:
            logger.error(f"Failed to load Rust library: {e}")
            raise
    
    def _setup_function_signatures(self):
        """C 함수 시그니처 설정"""
        # create_crypto_service
        self.lib.create_crypto_service.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t
        ]
        self.lib.create_crypto_service.restype = ctypes.c_void_p
        
        # encrypt_file_ffi
        self.lib.encrypt_file_ffi.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p
        ]
        self.lib.encrypt_file_ffi.restype = ctypes.c_void_p
        
        # decrypt_file_ffi
        self.lib.decrypt_file_ffi.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p
        ]
        self.lib.decrypt_file_ffi.restype = ctypes.c_void_p
        
        # free_crypto_service
        self.lib.free_crypto_service.argtypes = [ctypes.c_void_p]
        self.lib.free_crypto_service.restype = None
    
    def _initialize_service(self):
        """암호화 서비스 초기화"""
        try:
            master_key_bytes = self.master_key.encode('utf-8')
            master_key_array = (ctypes.c_uint8 * len(master_key_bytes)).from_buffer_copy(master_key_bytes)
            
            self.service = self.lib.create_crypto_service(
                master_key_array,
                len(master_key_bytes)
            )
            
            if not self.service:
                raise RuntimeError("Failed to create crypto service")
            
            logger.info("Crypto service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize crypto service: {e}")
            raise
    
    def create_key(
        self, 
        key_id: str, 
        algorithm: str = "AES256GCM",
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """새 암호화 키 생성"""
        try:
            # TODO: Rust 함수 호출 구현
            key_info = {
                "key_id": key_id,
                "algorithm": algorithm,
                "key_size": 32,
                "created_at": datetime.utcnow().timestamp(),
                "expires_at": expires_at.timestamp() if expires_at else None,
                "is_active": True
            }
            
            logger.info(f"Created encryption key: {key_id}")
            return key_info
            
        except Exception as e:
            logger.error(f"Failed to create key {key_id}: {e}")
            raise
    
    def encrypt_file(
        self, 
        input_path: str, 
        output_path: str, 
        key_id: str
    ) -> Dict[str, Any]:
        """파일 암호화"""
        try:
            input_path_bytes = input_path.encode('utf-8')
            output_path_bytes = output_path.encode('utf-8')
            key_id_bytes = key_id.encode('utf-8')
            
            # Rust 함수 호출
            result_ptr = self.lib.encrypt_file_ffi(
                self.service,
                input_path_bytes,
                output_path_bytes,
                key_id_bytes
            )
            
            if not result_ptr:
                raise RuntimeError("Encryption failed")
            
            # 결과 파싱 (간소화)
            result = {
                "success": True,
                "encrypted_file_path": output_path,
                "key_id": key_id,
                "algorithm": "AES256GCM",
                "file_hash": self._calculate_file_hash(input_path),
                "encryption_time_ms": 0,
                "error_message": None
            }
            
            logger.info(f"File encrypted: {input_path} -> {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to encrypt file {input_path}: {e}")
            return {
                "success": False,
                "encrypted_file_path": None,
                "key_id": key_id,
                "algorithm": "AES256GCM",
                "file_hash": "",
                "encryption_time_ms": 0,
                "error_message": str(e)
            }
    
    def decrypt_file(
        self, 
        input_path: str, 
        output_path: str, 
        key_id: str
    ) -> Dict[str, Any]:
        """파일 복호화"""
        try:
            input_path_bytes = input_path.encode('utf-8')
            output_path_bytes = output_path.encode('utf-8')
            key_id_bytes = key_id.encode('utf-8')
            
            # Rust 함수 호출
            result_ptr = self.lib.decrypt_file_ffi(
                self.service,
                input_path_bytes,
                output_path_bytes,
                key_id_bytes
            )
            
            if not result_ptr:
                raise RuntimeError("Decryption failed")
            
            # 결과 파싱 (간소화)
            result = {
                "success": True,
                "decrypted_file_path": output_path,
                "file_hash": self._calculate_file_hash(output_path),
                "decryption_time_ms": 0,
                "error_message": None
            }
            
            logger.info(f"File decrypted: {input_path} -> {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to decrypt file {input_path}: {e}")
            return {
                "success": False,
                "decrypted_file_path": None,
                "file_hash": "",
                "decryption_time_ms": 0,
                "error_message": str(e)
            }
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        import hashlib
        
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate file hash: {e}")
            return ""
    
    def get_key_info(self, key_id: str) -> Dict[str, Any]:
        """키 정보 조회"""
        # TODO: Rust 함수 호출 구현
        return {
            "key_id": key_id,
            "algorithm": "AES256GCM",
            "key_size": 32,
            "created_at": datetime.utcnow().timestamp(),
            "expires_at": None,
            "is_active": True
        }
    
    def delete_key(self, key_id: str) -> bool:
        """키 삭제"""
        try:
            # TODO: Rust 함수 호출 구현
            logger.info(f"Deleted encryption key: {key_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete key {key_id}: {e}")
            return False
    
    def __del__(self):
        """소멸자 - 리소스 정리"""
        if hasattr(self, 'service') and self.service:
            try:
                self.lib.free_crypto_service(self.service)
            except Exception as e:
                logger.error(f"Failed to free crypto service: {e}")


# 전역 암호화 엔진 인스턴스
crypto_engine = None


def get_crypto_engine() -> CryptoEngine:
    """암호화 엔진 인스턴스 반환"""
    global crypto_engine
    if crypto_engine is None:
        crypto_engine = CryptoEngine()
    return crypto_engine


def encrypt_file(input_path: str, output_path: str, key_id: str) -> Dict[str, Any]:
    """파일 암호화 헬퍼 함수"""
    engine = get_crypto_engine()
    return engine.encrypt_file(input_path, output_path, key_id)


def decrypt_file(input_path: str, output_path: str, key_id: str) -> Dict[str, Any]:
    """파일 복호화 헬퍼 함수"""
    engine = get_crypto_engine()
    return engine.decrypt_file(input_path, output_path, key_id)


def create_encryption_key(key_id: str, algorithm: str = "AES256GCM") -> Dict[str, Any]:
    """암호화 키 생성 헬퍼 함수"""
    engine = get_crypto_engine()
    return engine.create_key(key_id, algorithm)


if __name__ == "__main__":
    # 테스트 코드
    import tempfile
    
    # 암호화 엔진 초기화
    engine = CryptoEngine()
    
    # 키 생성
    key_info = engine.create_key("test_key_001")
    print(f"Created key: {key_info}")
    
    # 테스트 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, Medical Cybersecurity System!")
        input_file = f.name
    
    encrypted_file = input_file + ".encrypted"
    decrypted_file = input_file + ".decrypted"
    
    try:
        # 파일 암호화
        encrypt_result = engine.encrypt_file(input_file, encrypted_file, "test_key_001")
        print(f"Encryption result: {encrypt_result}")
        
        # 파일 복호화
        decrypt_result = engine.decrypt_file(encrypted_file, decrypted_file, "test_key_001")
        print(f"Decryption result: {decrypt_result}")
        
        # 원본과 복호화된 파일 비교
        with open(input_file, 'r') as f1, open(decrypted_file, 'r') as f2:
            original = f1.read()
            decrypted = f2.read()
            print(f"Original: {original}")
            print(f"Decrypted: {decrypted}")
            print(f"Match: {original == decrypted}")
    
    finally:
        # 정리
        for file_path in [input_file, encrypted_file, decrypted_file]:
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass