/*
 * Medical Cybersecurity System - Rust Encryption Engine
 * 
 * 고성능 파일 암호화 및 키 관리 시스템
 * HIPAA, GDPR 규정 준수
 */

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, NewAead};
use argon2::{Argon2, PasswordHash, PasswordHasher, PasswordVerifier};
use argon2::password_hash::{rand_core::OsRng, SaltString};
use chacha20poly1305::{ChaCha20Poly1305, Key as ChaChaKey, Nonce as ChaChaNonce};
use sha2::{Sha256, Digest};
use serde::{Deserialize, Serialize};
use anyhow::{Result, Context};
use tokio::fs;
use tokio::sync::RwLock;

/// 암호화 알고리즘 타입
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EncryptionAlgorithm {
    Aes256Gcm,
    ChaCha20Poly1305,
}

/// 키 정보 구조체
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyInfo {
    pub key_id: String,
    pub algorithm: EncryptionAlgorithm,
    pub key_size: usize,
    pub created_at: u64,
    pub expires_at: Option<u64>,
    pub is_active: bool,
}

/// 암호화 결과
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptionResult {
    pub success: bool,
    pub encrypted_file_path: Option<String>,
    pub key_id: String,
    pub algorithm: EncryptionAlgorithm,
    pub file_hash: String,
    pub encryption_time_ms: u64,
    pub error_message: Option<String>,
}

/// 복호화 결과
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecryptionResult {
    pub success: bool,
    pub decrypted_file_path: Option<String>,
    pub file_hash: String,
    pub decryption_time_ms: u64,
    pub error_message: Option<String>,
}

/// 키 관리자
pub struct KeyManager {
    keys: Arc<RwLock<HashMap<String, Vec<u8>>>>,
    key_info: Arc<RwLock<HashMap<String, KeyInfo>>>,
    master_key: Vec<u8>,
}

impl KeyManager {
    pub fn new(master_key: &[u8]) -> Self {
        Self {
            keys: Arc::new(RwLock::new(HashMap::new())),
            key_info: Arc::new(RwLock::new(HashMap::new())),
            master_key: master_key.to_vec(),
        }
    }

    /// 새 암호화 키 생성
    pub async fn generate_key(
        &self,
        key_id: String,
        algorithm: EncryptionAlgorithm,
        expires_at: Option<u64>,
    ) -> Result<KeyInfo> {
        let key_size = match algorithm {
            EncryptionAlgorithm::Aes256Gcm => 32,
            EncryptionAlgorithm::ChaCha20Poly1305 => 32,
        };

        let key = self.generate_random_bytes(key_size);
        let created_at = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        let key_info = KeyInfo {
            key_id: key_id.clone(),
            algorithm,
            key_size,
            created_at,
            expires_at,
            is_active: true,
        };

        // 키 암호화 (마스터 키로)
        let encrypted_key = self.encrypt_key(&key)?;

        // 저장
        {
            let mut keys = self.keys.write().await;
            keys.insert(key_id.clone(), encrypted_key);
        }

        {
            let mut key_info_map = self.key_info.write().await;
            key_info_map.insert(key_id, key_info.clone());
        }

        Ok(key_info)
    }

    /// 키 조회
    pub async fn get_key(&self, key_id: &str) -> Result<Vec<u8>> {
        let encrypted_key = {
            let keys = self.keys.read().await;
            keys.get(key_id)
                .ok_or_else(|| anyhow::anyhow!("Key not found: {}", key_id))?
                .clone()
        };

        self.decrypt_key(&encrypted_key)
    }

    /// 키 정보 조회
    pub async fn get_key_info(&self, key_id: &str) -> Result<KeyInfo> {
        let key_info = {
            let key_info_map = self.key_info.read().await;
            key_info_map.get(key_id)
                .ok_or_else(|| anyhow::anyhow!("Key info not found: {}", key_id))?
                .clone()
        };

        Ok(key_info)
    }

    /// 키 삭제
    pub async fn delete_key(&self, key_id: &str) -> Result<()> {
        {
            let mut keys = self.keys.write().await;
            keys.remove(key_id);
        }

        {
            let mut key_info_map = self.key_info.write().await;
            key_info_map.remove(key_id);
        }

        Ok(())
    }

    /// 랜덤 바이트 생성
    fn generate_random_bytes(&self, size: usize) -> Vec<u8> {
        use rand::RngCore;
        let mut bytes = vec![0u8; size];
        rand::thread_rng().fill_bytes(&mut bytes);
        bytes
    }

    /// 키 암호화 (마스터 키 사용)
    fn encrypt_key(&self, key: &[u8]) -> Result<Vec<u8>> {
        let cipher = Aes256Gcm::new(Key::from_slice(&self.master_key));
        let nonce = self.generate_random_bytes(12);
        let nonce = Nonce::from_slice(&nonce);
        
        let ciphertext = cipher.encrypt(nonce, key)
            .context("Failed to encrypt key")?;
        
        let mut result = nonce.to_vec();
        result.extend_from_slice(&ciphertext);
        Ok(result)
    }

    /// 키 복호화 (마스터 키 사용)
    fn decrypt_key(&self, encrypted_key: &[u8]) -> Result<Vec<u8>> {
        if encrypted_key.len() < 12 {
            return Err(anyhow::anyhow!("Invalid encrypted key format"));
        }

        let (nonce_bytes, ciphertext) = encrypted_key.split_at(12);
        let nonce = Nonce::from_slice(nonce_bytes);
        
        let cipher = Aes256Gcm::new(Key::from_slice(&self.master_key));
        let plaintext = cipher.decrypt(nonce, ciphertext)
            .context("Failed to decrypt key")?;
        
        Ok(plaintext)
    }
}

/// 파일 암호화기
pub struct FileEncryptor {
    key_manager: Arc<KeyManager>,
}

impl FileEncryptor {
    pub fn new(key_manager: Arc<KeyManager>) -> Self {
        Self { key_manager }
    }

    /// 파일 암호화
    pub async fn encrypt_file(
        &self,
        input_path: &Path,
        output_path: &Path,
        key_id: &str,
    ) -> Result<EncryptionResult> {
        let start_time = SystemTime::now();

        // 키 조회
        let key = self.key_manager.get_key(key_id).await?;
        let key_info = self.key_manager.get_key_info(key_id).await?;

        // 파일 읽기
        let file_data = fs::read(input_path).await
            .context("Failed to read input file")?;

        // 파일 해시 계산
        let file_hash = self.calculate_file_hash(&file_data);

        // 암호화 실행
        let encrypted_data = match key_info.algorithm {
            EncryptionAlgorithm::Aes256Gcm => {
                self.encrypt_aes256gcm(&file_data, &key)?
            }
            EncryptionAlgorithm::ChaCha20Poly1305 => {
                self.encrypt_chacha20poly1305(&file_data, &key)?
            }
        };

        // 암호화된 파일 저장
        fs::write(output_path, &encrypted_data).await
            .context("Failed to write encrypted file")?;

        let encryption_time = start_time.elapsed().unwrap().as_millis() as u64;

        Ok(EncryptionResult {
            success: true,
            encrypted_file_path: Some(output_path.to_string_lossy().to_string()),
            key_id: key_id.to_string(),
            algorithm: key_info.algorithm,
            file_hash,
            encryption_time_ms: encryption_time,
            error_message: None,
        })
    }

    /// 파일 복호화
    pub async fn decrypt_file(
        &self,
        input_path: &Path,
        output_path: &Path,
        key_id: &str,
    ) -> Result<DecryptionResult> {
        let start_time = SystemTime::now();

        // 키 조회
        let key = self.key_manager.get_key(key_id).await?;
        let key_info = self.key_manager.get_key_info(key_id).await?;

        // 암호화된 파일 읽기
        let encrypted_data = fs::read(input_path).await
            .context("Failed to read encrypted file")?;

        // 복호화 실행
        let decrypted_data = match key_info.algorithm {
            EncryptionAlgorithm::Aes256Gcm => {
                self.decrypt_aes256gcm(&encrypted_data, &key)?
            }
            EncryptionAlgorithm::ChaCha20Poly1305 => {
                self.decrypt_chacha20poly1305(&encrypted_data, &key)?
            }
        };

        // 복호화된 파일 저장
        fs::write(output_path, &decrypted_data).await
            .context("Failed to write decrypted file")?;

        // 파일 해시 계산
        let file_hash = self.calculate_file_hash(&decrypted_data);

        let decryption_time = start_time.elapsed().unwrap().as_millis() as u64;

        Ok(DecryptionResult {
            success: true,
            decrypted_file_path: Some(output_path.to_string_lossy().to_string()),
            file_hash,
            decryption_time_ms: decryption_time,
            error_message: None,
        })
    }

    /// AES-256-GCM 암호화
    fn encrypt_aes256gcm(&self, data: &[u8], key: &[u8]) -> Result<Vec<u8>> {
        let cipher = Aes256Gcm::new(Key::from_slice(key));
        let nonce = self.generate_random_bytes(12);
        let nonce = Nonce::from_slice(&nonce);
        
        let ciphertext = cipher.encrypt(nonce, data)
            .context("Failed to encrypt with AES-256-GCM")?;
        
        let mut result = nonce.to_vec();
        result.extend_from_slice(&ciphertext);
        Ok(result)
    }

    /// AES-256-GCM 복호화
    fn decrypt_aes256gcm(&self, encrypted_data: &[u8], key: &[u8]) -> Result<Vec<u8>> {
        if encrypted_data.len() < 12 {
            return Err(anyhow::anyhow!("Invalid encrypted data format"));
        }

        let (nonce_bytes, ciphertext) = encrypted_data.split_at(12);
        let nonce = Nonce::from_slice(nonce_bytes);
        
        let cipher = Aes256Gcm::new(Key::from_slice(key));
        let plaintext = cipher.decrypt(nonce, ciphertext)
            .context("Failed to decrypt with AES-256-GCM")?;
        
        Ok(plaintext)
    }

    /// ChaCha20-Poly1305 암호화
    fn encrypt_chacha20poly1305(&self, data: &[u8], key: &[u8]) -> Result<Vec<u8>> {
        let cipher = ChaCha20Poly1305::new(ChaChaKey::from_slice(key));
        let nonce = self.generate_random_bytes(12);
        let nonce = ChaChaNonce::from_slice(&nonce);
        
        let ciphertext = cipher.encrypt(nonce, data)
            .context("Failed to encrypt with ChaCha20-Poly1305")?;
        
        let mut result = nonce.to_vec();
        result.extend_from_slice(&ciphertext);
        Ok(result)
    }

    /// ChaCha20-Poly1305 복호화
    fn decrypt_chacha20poly1305(&self, encrypted_data: &[u8], key: &[u8]) -> Result<Vec<u8>> {
        if encrypted_data.len() < 12 {
            return Err(anyhow::anyhow!("Invalid encrypted data format"));
        }

        let (nonce_bytes, ciphertext) = encrypted_data.split_at(12);
        let nonce = ChaChaNonce::from_slice(nonce_bytes);
        
        let cipher = ChaCha20Poly1305::new(ChaChaKey::from_slice(key));
        let plaintext = cipher.decrypt(nonce, ciphertext)
            .context("Failed to decrypt with ChaCha20-Poly1305")?;
        
        Ok(plaintext)
    }

    /// 파일 해시 계산 (SHA-256)
    fn calculate_file_hash(&self, data: &[u8]) -> String {
        let mut hasher = Sha256::new();
        hasher.update(data);
        format!("{:x}", hasher.finalize())
    }

    /// 랜덤 바이트 생성
    fn generate_random_bytes(&self, size: usize) -> Vec<u8> {
        use rand::RngCore;
        let mut bytes = vec![0u8; size];
        rand::thread_rng().fill_bytes(&mut bytes);
        bytes
    }
}

/// 암호화 서비스 메인 구조체
pub struct CryptoService {
    key_manager: Arc<KeyManager>,
    file_encryptor: FileEncryptor,
}

impl CryptoService {
    pub fn new(master_key: &[u8]) -> Self {
        let key_manager = Arc::new(KeyManager::new(master_key));
        let file_encryptor = FileEncryptor::new(key_manager.clone());
        
        Self {
            key_manager,
            file_encryptor,
        }
    }

    /// 키 생성
    pub async fn create_key(
        &self,
        key_id: String,
        algorithm: EncryptionAlgorithm,
        expires_at: Option<u64>,
    ) -> Result<KeyInfo> {
        self.key_manager.generate_key(key_id, algorithm, expires_at).await
    }

    /// 파일 암호화
    pub async fn encrypt_file(
        &self,
        input_path: &Path,
        output_path: &Path,
        key_id: &str,
    ) -> Result<EncryptionResult> {
        self.file_encryptor.encrypt_file(input_path, output_path, key_id).await
    }

    /// 파일 복호화
    pub async fn decrypt_file(
        &self,
        input_path: &Path,
        output_path: &Path,
        key_id: &str,
    ) -> Result<DecryptionResult> {
        self.file_encryptor.decrypt_file(input_path, output_path, key_id).await
    }

    /// 키 정보 조회
    pub async fn get_key_info(&self, key_id: &str) -> Result<KeyInfo> {
        self.key_manager.get_key_info(key_id).await
    }

    /// 키 삭제
    pub async fn delete_key(&self, key_id: &str) -> Result<()> {
        self.key_manager.delete_key(key_id).await
    }
}

// C FFI 인터페이스 (Python 바인딩용)
#[no_mangle]
pub extern "C" fn create_crypto_service(master_key: *const u8, key_len: usize) -> *mut CryptoService {
    let key_slice = unsafe { std::slice::from_raw_parts(master_key, key_len) };
    let service = Box::new(CryptoService::new(key_slice));
    Box::into_raw(service)
}

#[no_mangle]
pub extern "C" fn encrypt_file_ffi(
    service: *mut CryptoService,
    input_path: *const i8,
    output_path: *const i8,
    key_id: *const i8,
) -> *mut EncryptionResult {
    // FFI 구현 (간소화)
    todo!("FFI implementation")
}

#[no_mangle]
pub extern "C" fn free_crypto_service(service: *mut CryptoService) {
    if !service.is_null() {
        unsafe {
            let _ = Box::from_raw(service);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[tokio::test]
    async fn test_encryption_decryption() {
        let master_key = b"test_master_key_32_bytes_long!";
        let service = CryptoService::new(master_key);

        // 키 생성
        let key_info = service.create_key(
            "test_key".to_string(),
            EncryptionAlgorithm::Aes256Gcm,
            None,
        ).await.unwrap();

        // 테스트 파일 생성
        let test_data = b"Hello, Medical Cybersecurity System!";
        let input_path = PathBuf::from("/tmp/test_input.txt");
        let encrypted_path = PathBuf::from("/tmp/test_encrypted.bin");
        let decrypted_path = PathBuf::from("/tmp/test_decrypted.txt");

        tokio::fs::write(&input_path, test_data).await.unwrap();

        // 암호화
        let encrypt_result = service.encrypt_file(
            &input_path,
            &encrypted_path,
            &key_info.key_id,
        ).await.unwrap();

        assert!(encrypt_result.success);

        // 복호화
        let decrypt_result = service.decrypt_file(
            &encrypted_path,
            &decrypted_path,
            &key_info.key_id,
        ).await.unwrap();

        assert!(decrypt_result.success);

        // 원본과 복호화된 데이터 비교
        let decrypted_data = tokio::fs::read(&decrypted_path).await.unwrap();
        assert_eq!(test_data, &decrypted_data[..]);

        // 정리
        let _ = tokio::fs::remove_file(&input_path).await;
        let _ = tokio::fs::remove_file(&encrypted_path).await;
        let _ = tokio::fs::remove_file(&decrypted_path).await;
    }
}