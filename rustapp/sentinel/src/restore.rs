use anyhow::{Context, Result};
use serde::Deserialize;
use std::fs;
use std::path::{Path, PathBuf};

use crate::backup::SnapshotManifest;
use crate::config::AppConfig;

fn object_path(store_dir: &Path, digest: &str) -> PathBuf {
    let (dir, file) = digest.split_at(2);
    store_dir.join("objects").join(dir).join(file)
}

fn latest_manifest_path(store_dir: &Path) -> Result<PathBuf> {
    let mut manifests: Vec<PathBuf> = fs::read_dir(store_dir.join("manifests"))?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|e| e.to_str()) == Some("json"))
        .collect();
    manifests.sort();
    manifests.last().cloned().ok_or_else(|| anyhow::anyhow!("No manifests found"))
}

pub async fn run_restore(_cfg: &AppConfig, store_dir: &Path, target_dir: &Path) -> Result<()> {
    fs::create_dir_all(target_dir)?;
    let manifest_path = latest_manifest_path(store_dir)?;
    let data = fs::read(&manifest_path)?;
    let manifest: SnapshotManifest = serde_json::from_slice(&data)?;

    for file in manifest.files.iter() {
        let src_obj = object_path(store_dir, &file.blake3);
        let dst_path = target_dir.join(&file.rel_path);
        if let Some(parent) = dst_path.parent() { fs::create_dir_all(parent)?; }
        fs::copy(&src_obj, &dst_path).with_context(|| format!("Copy {} -> {}", src_obj.display(), dst_path.display()))?;
    }
    println!("Restored snapshot {} to {}", manifest.snapshot_id, target_dir.display());
    Ok(())
}

