use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use tokio::fs;
use tracing::debug;

use crate::backup::{BackupEngine, BackupVersion};
use crate::crypto::Crypto;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupInfo {
    pub file_path: String,
    pub versions: Vec<BackupVersion>,
}

pub struct Storage {
    storage_path: PathBuf,
    backup_engine: BackupEngine,
    crypto: Crypto,
    encryption_key: Vec<u8>,
}

impl Storage {
    pub fn new(storage_path: &str) -> Result<Self> {
        let path = PathBuf::from(storage_path);
        std::fs::create_dir_all(&path)?;

        let crypto = Crypto::new();
        let encryption_key = crypto.generate_key()?;

        Ok(Storage {
            storage_path: path,
            backup_engine: BackupEngine::new(4096),
            crypto,
            encryption_key,
        })
    }

    pub async fn backup_file(&self, file_path: &Path) -> Result<()> {
        if !file_path.exists() {
            return Ok(()); // File deleted, skip backup
        }

        // Create backup version
        let backup_version = self.backup_engine.create_backup(&file_path.to_path_buf())?;

        // Create storage path for this file
        let storage_file_path = self.get_storage_path(file_path);
        fs::create_dir_all(storage_file_path.parent().unwrap()).await?;

        // Load existing backup info or create new
        let mut backup_info = self.load_backup_info(file_path).await
            .unwrap_or_else(|_| BackupInfo {
                file_path: file_path.to_string_lossy().to_string(),
                versions: Vec::new(),
            });

        // Check if file actually changed
        if let Some(last_version) = backup_info.versions.last() {
            if last_version.file_hash == backup_version.file_hash {
                debug!("File unchanged, skipping backup: {:?}", file_path);
                return Ok(());
            }
        }

        // Store blocks
        let file_data = fs::read(file_path).await?;
        for (idx, chunk) in file_data.chunks(4096).enumerate() {
            let block_hash = &backup_version.block_hashes[idx];
            let block_path = self.get_block_path(block_hash);

            // Only store if block doesn't exist (deduplication)
            if !block_path.exists() {
                // Compress and encrypt block
                let compressed = self.backup_engine.compress(chunk)?;
                let encrypted = self.backup_engine.encrypt_block(&compressed, &self.encryption_key)?;
                
                fs::create_dir_all(block_path.parent().unwrap()).await?;
                fs::write(&block_path, encrypted).await?;
            }
        }

        // Add version and save backup info
        let version_number = backup_info.versions.len() as u64 + 1;
        let mut new_version = backup_version;
        new_version.version = version_number;
        
        backup_info.versions.push(new_version);

        // Keep only last N versions
        if backup_info.versions.len() > 100 {
            backup_info.versions.drain(0..10); // Remove oldest 10
        }

        self.save_backup_info(file_path, &backup_info).await?;
        
        debug!("Backed up {:?} - version {}", file_path, version_number);
        Ok(())
    }

    pub async fn restore_file(&self, file_path: &str, version: Option<u64>) -> Result<()> {
        let path = PathBuf::from(file_path);
        let backup_info = self.load_backup_info(&path).await?;

        if backup_info.versions.is_empty() {
            anyhow::bail!("No backup versions found");
        }

        // Get requested version or latest
        let backup_version = if let Some(v) = version {
            backup_info.versions.iter()
                .find(|ver| ver.version == v)
                .context("Version not found")?
        } else {
            backup_info.versions.last().unwrap()
        };

        // Reconstruct file from blocks
        let mut file_data = Vec::new();
        
        for block_hash in &backup_version.block_hashes {
            let block_path = self.get_block_path(block_hash);
            let encrypted_block = fs::read(&block_path).await
                .context(format!("Block not found: {}", block_hash))?;
            
            // Decrypt and decompress
            let compressed = self.backup_engine.decrypt_block(&encrypted_block, &self.encryption_key)?;
            let block_data = self.backup_engine.decompress(&compressed)?;
            
            file_data.extend_from_slice(&block_data);
        }

        // Write restored file
        fs::write(&path, file_data).await?;
        
        debug!("Restored {:?} from version {}", path, backup_version.version);
        Ok(())
    }

    pub async fn list_backups(&self) -> Result<Vec<BackupInfo>> {
        let mut backups = Vec::new();
        
        let mut entries = fs::read_dir(&self.storage_path).await?;
        while let Some(entry) = entries.next_entry().await? {
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) == Some("json") {
                if let Ok(content) = fs::read_to_string(&path).await {
                    if let Ok(info) = serde_json::from_str::<BackupInfo>(&content) {
                        backups.push(info);
                    }
                }
            }
        }

        Ok(backups)
    }

    pub async fn backup_count(&self) -> Result<usize> {
        let backups = self.list_backups().await?;
        let total: usize = backups.iter().map(|b| b.versions.len()).sum();
        Ok(total)
    }

    fn get_storage_path(&self, file_path: &Path) -> PathBuf {
        let hash = self.crypto.hash(file_path.to_string_lossy().as_bytes());
        self.storage_path.join(format!("{}.json", hash))
    }

    fn get_block_path(&self, block_hash: &str) -> PathBuf {
        // Use first 2 chars as subdirectory for better file system performance
        let subdir = &block_hash[..2];
        self.storage_path.join("blocks").join(subdir).join(block_hash)
    }

    async fn load_backup_info(&self, file_path: &Path) -> Result<BackupInfo> {
        let storage_path = self.get_storage_path(file_path);
        let content = fs::read_to_string(storage_path).await?;
        let info = serde_json::from_str(&content)?;
        Ok(info)
    }

    async fn save_backup_info(&self, file_path: &Path, info: &BackupInfo) -> Result<()> {
        let storage_path = self.get_storage_path(file_path);
        let content = serde_json::to_string_pretty(info)?;
        fs::write(storage_path, content).await?;
        Ok(())
    }
}
