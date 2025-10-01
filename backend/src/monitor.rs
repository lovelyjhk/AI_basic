use anyhow::Result;
use notify::{Event, RecommendedWatcher, RecursiveMode, Watcher};
use std::path::PathBuf;
use std::sync::mpsc;
use tokio::sync::mpsc as tokio_mpsc;
use tracing::{debug, error};

use crate::config::Config;

#[derive(Debug, Clone)]
pub struct FileEvent {
    pub path: PathBuf,
    pub event_type: FileEventType,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone)]
pub enum FileEventType {
    Created,
    Modified,
    Deleted,
    Renamed,
}

pub struct FileMonitor {
    _watcher: RecommendedWatcher,
    receiver: tokio_mpsc::UnboundedReceiver<FileEvent>,
}

impl FileMonitor {
    pub fn new(config: Config) -> Result<Self> {
        let (tx, rx) = mpsc::channel();
        let (async_tx, async_rx) = tokio_mpsc::unbounded_channel();

        // Create file system watcher
        let mut watcher = notify::recommended_watcher(move |res: Result<Event, _>| {
            match res {
                Ok(event) => {
                    if let Some(file_event) = Self::convert_event(event) {
                        let _ = tx.send(file_event);
                    }
                }
                Err(e) => error!("Watch error: {:?}", e),
            }
        })?;

        // Watch all configured paths
        for path in &config.monitoring.watch_paths {
            let path_buf = PathBuf::from(path);
            if path_buf.exists() {
                watcher.watch(&path_buf, RecursiveMode::Recursive)?;
                debug!("Watching: {}", path);
            } else {
                // Create directory if it doesn't exist
                std::fs::create_dir_all(&path_buf)?;
                watcher.watch(&path_buf, RecursiveMode::Recursive)?;
                debug!("Created and watching: {}", path);
            }
        }

        // Spawn thread to convert sync events to async
        let extensions = config.monitoring.file_extensions.clone();
        tokio::spawn(async move {
            while let Ok(event) = rx.recv() {
                // Filter by file extension
                if let Some(ext) = event.path.extension() {
                    let ext_str = format!(".{}", ext.to_string_lossy());
                    if extensions.is_empty() || extensions.contains(&ext_str) {
                        let _ = async_tx.send(event);
                    }
                }
            }
        });

        Ok(FileMonitor {
            _watcher: watcher,
            receiver: async_rx,
        })
    }

    fn convert_event(event: Event) -> Option<FileEvent> {
        let timestamp = chrono::Utc::now();
        
        match event.kind {
            notify::EventKind::Create(_) => {
                event.paths.first().map(|path| FileEvent {
                    path: path.clone(),
                    event_type: FileEventType::Created,
                    timestamp,
                })
            }
            notify::EventKind::Modify(_) => {
                event.paths.first().map(|path| FileEvent {
                    path: path.clone(),
                    event_type: FileEventType::Modified,
                    timestamp,
                })
            }
            notify::EventKind::Remove(_) => {
                event.paths.first().map(|path| FileEvent {
                    path: path.clone(),
                    event_type: FileEventType::Deleted,
                    timestamp,
                })
            }
            _ => None,
        }
    }

    pub async fn next_event(&mut self) -> Option<FileEvent> {
        self.receiver.recv().await
    }
}
