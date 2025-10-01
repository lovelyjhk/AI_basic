use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub source_dir: PathBuf,
    pub restore_dir: PathBuf,
    pub store_dir: PathBuf,
    pub key_path: PathBuf,
    pub ai_url: String,
    #[serde(default = "default_chunk_size")]
    pub chunk_size: usize,
}

fn default_chunk_size() -> usize { 1_048_576 }

impl AppConfig {
    pub fn load(path: &Path) -> Result<Self> {
        let text = fs::read_to_string(path)?;
        let cfg: AppConfig = toml::from_str(&text)?;
        Ok(cfg)
    }
}

