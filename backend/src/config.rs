use serde::{Deserialize, Serialize};
use std::fs;
use anyhow::Result;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub monitoring: MonitoringConfig,
    pub detection: DetectionConfig,
    pub backup: BackupConfig,
    pub encryption: EncryptionConfig,
    pub alerts: AlertsConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonitoringConfig {
    pub watch_paths: Vec<String>,
    pub file_extensions: Vec<String>,
    pub event_buffer_size: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetectionConfig {
    pub entropy_threshold: f64,
    pub rapid_change_threshold: usize,
    pub suspicious_extensions: Vec<String>,
    pub time_window_seconds: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupConfig {
    pub incremental_interval: u64,
    pub retention_versions: usize,
    pub block_size: usize,
    pub compression_enabled: bool,
    pub storage_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptionConfig {
    pub algorithm: String,
    pub key_derivation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlertsConfig {
    pub webhook_url: Option<String>,
    pub email_recipients: Vec<String>,
    pub sms_numbers: Vec<String>,
}

impl Config {
    pub fn load(path: &str) -> Result<Self> {
        let content = fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        Ok(config)
    }
}

impl Default for Config {
    fn default() -> Self {
        Config {
            monitoring: MonitoringConfig {
                watch_paths: vec!["./test_medical_data".to_string()],
                file_extensions: vec![
                    ".dcm".to_string(),
                    ".hl7".to_string(),
                    ".xml".to_string(),
                    ".json".to_string(),
                    ".db".to_string(),
                ],
                event_buffer_size: 10000,
            },
            detection: DetectionConfig {
                entropy_threshold: 7.5,
                rapid_change_threshold: 50,
                suspicious_extensions: vec![
                    ".locked".to_string(),
                    ".encrypted".to_string(),
                    ".crypto".to_string(),
                    ".crypt".to_string(),
                    ".enc".to_string(),
                ],
                time_window_seconds: 60,
            },
            backup: BackupConfig {
                incremental_interval: 60,
                retention_versions: 100,
                block_size: 4096,
                compression_enabled: true,
                storage_path: "./backups".to_string(),
            },
            encryption: EncryptionConfig {
                algorithm: "AES-256-GCM".to_string(),
                key_derivation: "Argon2id".to_string(),
            },
            alerts: AlertsConfig {
                webhook_url: None,
                email_recipients: vec![],
                sms_numbers: vec![],
            },
        }
    }
}
