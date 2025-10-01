use anyhow::{Context, Result};
use blake3::Hasher;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

use crate::config::AppConfig;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SnapshotManifest {
    pub snapshot_id: String,
    pub created_at_utc: String,
    pub files: Vec<FileEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileEntry {
    pub rel_path: String,
    pub size: u64,
    pub blake3: String,
}

fn hash_file(path: &Path) -> Result<(String, u64)> {
    let mut f = fs::File::open(path)?;
    let mut hasher = Hasher::new();
    let mut buf = vec![0u8; 1_048_576];
    let mut total = 0u64;
    loop {
        let n = f.read(&mut buf)?;
        if n == 0 { break; }
        hasher.update(&buf[..n]);
        total += n as u64;
    }
    Ok((hasher.finalize().to_hex().to_string(), total))
}

fn ensure_dir(path: &Path) -> Result<()> {
    fs::create_dir_all(path)?;
    Ok(())
}

fn object_path(store_dir: &Path, digest: &str) -> PathBuf {
    let (dir, file) = digest.split_at(2);
    store_dir.join("objects").join(dir).join(file)
}

fn write_object_if_missing(store_dir: &Path, src: &Path, digest: &str) -> Result<()> {
    let obj_path = object_path(store_dir, digest);
    if obj_path.exists() { return Ok(()); }
    if let Some(parent) = obj_path.parent() { ensure_dir(parent)?; }
    fs::copy(src, &obj_path).with_context(|| format!("Copying {} to object {}", src.display(), obj_path.display()))?;
    Ok(())
}

pub async fn run_backup(cfg: &AppConfig, source_dir: &Path, store_dir: &Path) -> Result<()> {
    ensure_dir(store_dir)?;
    ensure_dir(&store_dir.join("objects"))?;
    ensure_dir(&store_dir.join("manifests"))?;

    let mut entries: Vec<FileEntry> = Vec::new();
    for entry in WalkDir::new(source_dir).follow_links(false).into_iter().filter_map(|e| e.ok()) {
        if !entry.file_type().is_file() { continue; }
        let path = entry.path();
        let rel = path.strip_prefix(source_dir).unwrap().to_string_lossy().to_string();
        let (digest, size) = hash_file(path)?;
        write_object_if_missing(store_dir, path, &digest)?;
        entries.push(FileEntry { rel_path: rel, size, blake3: digest });
    }

    let snapshot_id = Utc::now().format("%Y%m%dT%H%M%S%.3fZ").to_string();
    let manifest = SnapshotManifest {
        snapshot_id: snapshot_id.clone(),
        created_at_utc: Utc::now().to_rfc3339(),
        files: entries,
    };
    let manifest_json = serde_json::to_vec_pretty(&manifest)?;
    let manifest_path = store_dir.join("manifests").join(format!("{}.json", snapshot_id));
    let mut f = fs::File::create(&manifest_path)?;
    f.write_all(&manifest_json)?;
    f.flush()?;
    println!("Snapshot created: {}", manifest_path.display());
    Ok(())
}

