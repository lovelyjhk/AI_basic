use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

use crate::crypto::Crypto;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupVersion {
    pub version: u64,
    pub timestamp: DateTime<Utc>,
    pub file_hash: String,
    pub block_hashes: Vec<String>,
    pub metadata: FileMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileMetadata {
    pub size: u64,
    pub permissions: u32,
    pub modified: DateTime<Utc>,
}

pub struct BackupEngine {
    crypto: Crypto,
    block_size: usize,
}

impl BackupEngine {
    pub fn new(block_size: usize) -> Self {
        BackupEngine {
            crypto: Crypto::new(),
            block_size,
        }
    }

    pub fn create_backup(&self, file_path: &PathBuf) -> Result<BackupVersion> {
        // Read file contents
        let data = std::fs::read(file_path)
            .context(format!("Failed to read file: {:?}", file_path))?;

        // Calculate file hash
        let file_hash = self.crypto.hash(&data);

        // Split into blocks and hash each
        let block_hashes = self.create_block_hashes(&data);

        // Get file metadata
        let metadata = self.get_metadata(file_path)?;

        Ok(BackupVersion {
            version: 1, // Will be set by storage layer
            timestamp: Utc::now(),
            file_hash,
            block_hashes,
            metadata,
        })
    }

    pub fn encrypt_block(&self, block: &[u8], key: &[u8]) -> Result<Vec<u8>> {
        self.crypto.encrypt(block, key)
    }

    pub fn decrypt_block(&self, encrypted_block: &[u8], key: &[u8]) -> Result<Vec<u8>> {
        self.crypto.decrypt(encrypted_block, key)
    }

    fn create_block_hashes(&self, data: &[u8]) -> Vec<String> {
        data.chunks(self.block_size)
            .map(|chunk| self.crypto.hash(chunk))
            .collect()
    }

    fn get_metadata(&self, file_path: &PathBuf) -> Result<FileMetadata> {
        let metadata = std::fs::metadata(file_path)
            .context("Failed to get file metadata")?;

        #[cfg(unix)]
        let permissions = {
            use std::os::unix::fs::PermissionsExt;
            metadata.permissions().mode()
        };

        #[cfg(not(unix))]
        let permissions = 0o644;

        let modified = metadata.modified()
            .context("Failed to get modification time")?;
        let modified_datetime: DateTime<Utc> = modified.into();

        Ok(FileMetadata {
            size: metadata.len(),
            permissions,
            modified: modified_datetime,
        })
    }

    pub fn calculate_incremental_changes(
        &self,
        current_data: &[u8],
        previous_blocks: &[String],
    ) -> Vec<usize> {
        let current_hashes = self.create_block_hashes(current_data);
        
        current_hashes
            .iter()
            .enumerate()
            .filter_map(|(idx, hash)| {
                if idx >= previous_blocks.len() || hash != &previous_blocks[idx] {
                    Some(idx)
                } else {
                    None
                }
            })
            .collect()
    }

    pub fn compress(&self, data: &[u8]) -> Result<Vec<u8>> {
        zstd::encode_all(data, 3).context("Compression failed")
    }

    pub fn decompress(&self, compressed: &[u8]) -> Result<Vec<u8>> {
        zstd::decode_all(compressed).context("Decompression failed")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn test_backup_creation() {
        let mut file = NamedTempFile::new().unwrap();
        file.write_all(b"Test medical data").unwrap();

        let engine = BackupEngine::new(4096);
        let backup = engine.create_backup(&file.path().to_path_buf()).unwrap();

        assert!(!backup.file_hash.is_empty());
        assert!(!backup.block_hashes.is_empty());
    }

    #[test]
    fn test_incremental_changes() {
        let engine = BackupEngine::new(10);
        
        let old_data = b"Hello World!!!";
        let new_data = b"Hello Rust!!!!";
        
        let old_hashes = old_data.chunks(10)
            .map(|chunk| engine.crypto.hash(chunk))
            .collect::<Vec<_>>();
        
        let changes = engine.calculate_incremental_changes(new_data, &old_hashes);
        
        // Second block should be different
        assert!(!changes.is_empty());
    }

    #[test]
    fn test_compression() {
        let engine = BackupEngine::new(4096);
        let data = vec![b'A'; 10000]; // Highly compressible

        let compressed = engine.compress(&data).unwrap();
        let decompressed = engine.decompress(&compressed).unwrap();

        assert_eq!(data, decompressed);
        assert!(compressed.len() < data.len());
    }
}
