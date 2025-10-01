use aes_gcm::aead::{Aead, KeyInit, OsRng};
use aes_gcm::{Aes256Gcm, Nonce};
use anyhow::{anyhow, Context, Result};
use rand::RngCore;
use std::fs;
use std::io::{Read, Write};
use std::path::Path;
use zeroize::Zeroize;

const KEY_LEN: usize = 32; // 256-bit
const NONCE_LEN: usize = 12; // GCM standard 96-bit

pub fn generate_key_file(path: &Path, force: bool) -> Result<()> {
    if path.exists() && !force {
        return Err(anyhow!("Key file already exists: {} (use --force)", path.display()));
    }
    let mut key = [0u8; KEY_LEN];
    OsRng.fill_bytes(&mut key);
    fs::write(path, &key)?;
    // Best effort: sync to disk
    if let Ok(f) = fs::OpenOptions::new().read(true).write(true).open(path) {
        let _ = f.sync_all();
    }
    // Zeroize stack copy
    let mut key_vec = key.to_vec();
    key_vec.zeroize();
    Ok(())
}

fn read_key(path: &Path) -> Result<[u8; KEY_LEN]> {
    let data = fs::read(path).with_context(|| format!("Reading key: {}", path.display()))?;
    if data.len() != KEY_LEN {
        return Err(anyhow!("Invalid key length: expected {} got {}", KEY_LEN, data.len()));
    }
    let mut key = [0u8; KEY_LEN];
    key.copy_from_slice(&data);
    Ok(key)
}

pub fn encrypt_file(key_path: &Path, input: &Path, output: &Path) -> Result<()> {
    let key_bytes = read_key(key_path)?;
    let cipher = Aes256Gcm::new_from_slice(&key_bytes)
        .map_err(|e| anyhow!("invalid AES key length: {}", e))?;

    let mut plaintext = Vec::new();
    fs::File::open(input)?.read_to_end(&mut plaintext)?;

    let mut nonce_bytes = [0u8; NONCE_LEN];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    let ciphertext = cipher
        .encrypt(nonce, plaintext.as_ref())
        .map_err(|e| anyhow!("encryption failed: {}", e))?;

    // Write: [nonce | ciphertext]
    let mut f = fs::File::create(output)?;
    f.write_all(&nonce_bytes)?;
    f.write_all(&ciphertext)?;
    f.flush()?;
    Ok(())
}

pub fn decrypt_file(key_path: &Path, input: &Path, output: &Path) -> Result<()> {
    let key_bytes = read_key(key_path)?;
    let cipher = Aes256Gcm::new_from_slice(&key_bytes)
        .map_err(|e| anyhow!("invalid AES key length: {}", e))?;

    let mut data = Vec::new();
    fs::File::open(input)?.read_to_end(&mut data)?;
    if data.len() < NONCE_LEN { return Err(anyhow!("Ciphertext too short")); }
    let (nonce_part, ct_part) = data.split_at(NONCE_LEN);
    let nonce = Nonce::from_slice(nonce_part);
    let plaintext = cipher
        .decrypt(nonce, ct_part)
        .map_err(|e| anyhow!("decryption failed: {}", e))?;

    fs::write(output, plaintext)?;
    Ok(())
}

