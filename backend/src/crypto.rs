use anyhow::{Context, Result};
use ring::aead::{Aad, BoundKey, Nonce, NonceSequence, OpeningKey, SealingKey, UnboundKey, AES_256_GCM};
use ring::error::Unspecified;
use ring::rand::{SecureRandom, SystemRandom};

const NONCE_LEN: usize = 12;

pub struct Crypto {
    rng: SystemRandom,
}

impl Crypto {
    pub fn new() -> Self {
        Crypto {
            rng: SystemRandom::new(),
        }
    }

    pub fn generate_key(&self) -> Result<Vec<u8>> {
        let mut key = vec![0u8; 32]; // 256 bits
        self.rng.fill(&mut key)
            .map_err(|_| anyhow::anyhow!("Failed to generate key"))?;
        Ok(key)
    }

    pub fn encrypt(&self, data: &[u8], key: &[u8]) -> Result<Vec<u8>> {
        // Generate random nonce
        let mut nonce_bytes = [0u8; NONCE_LEN];
        self.rng.fill(&mut nonce_bytes)
            .map_err(|_| anyhow::anyhow!("Failed to generate nonce"))?;

        // Create sealing key
        let unbound_key = UnboundKey::new(&AES_256_GCM, key)
            .map_err(|_| anyhow::anyhow!("Failed to create encryption key"))?;
        let nonce_sequence = OneNonceSequence::new(nonce_bytes);
        let mut sealing_key = SealingKey::new(unbound_key, nonce_sequence);

        // Prepare output buffer
        let mut encrypted = data.to_vec();
        sealing_key
            .seal_in_place_append_tag(Aad::empty(), &mut encrypted)
            .map_err(|_| anyhow::anyhow!("Encryption failed"))?;

        // Prepend nonce to encrypted data
        let mut output = nonce_bytes.to_vec();
        output.extend_from_slice(&encrypted);
        
        Ok(output)
    }

    pub fn decrypt(&self, encrypted_data: &[u8], key: &[u8]) -> Result<Vec<u8>> {
        if encrypted_data.len() < NONCE_LEN {
            anyhow::bail!("Invalid encrypted data: too short");
        }

        // Extract nonce
        let (nonce_bytes, ciphertext) = encrypted_data.split_at(NONCE_LEN);
        let nonce_array: [u8; NONCE_LEN] = nonce_bytes.try_into()
            .map_err(|_| anyhow::anyhow!("Invalid nonce length"))?;

        // Create opening key
        let unbound_key = UnboundKey::new(&AES_256_GCM, key)
            .map_err(|_| anyhow::anyhow!("Failed to create decryption key"))?;
        let nonce_sequence = OneNonceSequence::new(nonce_array);
        let mut opening_key = OpeningKey::new(unbound_key, nonce_sequence);

        // Decrypt
        let mut decrypted = ciphertext.to_vec();
        let decrypted_data = opening_key
            .open_in_place(Aad::empty(), &mut decrypted)
            .map_err(|_| anyhow::anyhow!("Decryption failed"))?;
        
        Ok(decrypted_data.to_vec())
    }

    pub fn hash(&self, data: &[u8]) -> String {
        // Using BLAKE3 for fast, secure hashing
        let hash = blake3::hash(data);
        hash.to_hex().to_string()
    }

    pub fn derive_key(&self, password: &str, salt: &[u8]) -> Result<Vec<u8>> {
        use argon2::{Argon2, PasswordHasher};
        use argon2::password_hash::SaltString;

        // Convert salt to SaltString  
        let salt_string = SaltString::encode_b64(salt)
            .map_err(|_| anyhow::anyhow!("Failed to encode salt"))?;

        let argon2 = Argon2::default();
        let password_hash = argon2
            .hash_password(password.as_bytes(), &salt_string)
            .map_err(|e| anyhow::anyhow!("Failed to derive key: {}", e))?;

        // Extract the hash bytes
        let hash = password_hash.hash
            .ok_or_else(|| anyhow::anyhow!("No hash in password hash"))?;
        
        Ok(hash.as_bytes().to_vec())
    }
}

// NonceSequence implementation for single-use nonce
struct OneNonceSequence {
    nonce: Option<[u8; NONCE_LEN]>,
}

impl OneNonceSequence {
    fn new(nonce: [u8; NONCE_LEN]) -> Self {
        OneNonceSequence { nonce: Some(nonce) }
    }
}

impl NonceSequence for OneNonceSequence {
    fn advance(&mut self) -> Result<Nonce, Unspecified> {
        let nonce = self.nonce.take().ok_or(Unspecified)?;
        Nonce::try_assume_unique_for_key(&nonce)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encryption_decryption() {
        let crypto = Crypto::new();
        let key = crypto.generate_key().unwrap();
        let plaintext = b"Hello, MedGuard!";

        let encrypted = crypto.encrypt(plaintext, &key).unwrap();
        let decrypted = crypto.decrypt(&encrypted, &key).unwrap();

        assert_eq!(plaintext, decrypted.as_slice());
    }

    #[test]
    fn test_hash_deterministic() {
        let crypto = Crypto::new();
        let data = b"Test data";

        let hash1 = crypto.hash(data);
        let hash2 = crypto.hash(data);

        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_different_data_different_hash() {
        let crypto = Crypto::new();
        
        let hash1 = crypto.hash(b"data1");
        let hash2 = crypto.hash(b"data2");

        assert_ne!(hash1, hash2);
    }
}
