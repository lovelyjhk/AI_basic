use crate::ai::{query_ai, AiResponse, Features};
use crate::config::AppConfig;
use anyhow::Result;
use notify::{recommended_watcher, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use reqwest::Client;
use std::collections::VecDeque;
use std::path::Path;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tokio::sync::mpsc;

struct RateWindow {
    timestamps: VecDeque<Instant>,
}

impl RateWindow {
    fn new() -> Self { Self { timestamps: VecDeque::new() } }
    fn push(&mut self, now: Instant) { self.timestamps.push_back(now); }
    fn prune(&mut self, now: Instant) {
        while let Some(front) = self.timestamps.front() {
            if now.duration_since(*front) > Duration::from_secs(1) { self.timestamps.pop_front(); } else { break; }
        }
    }
    fn per_second(&mut self, now: Instant) -> f32 {
        self.prune(now);
        self.timestamps.len() as f32
    }
}

pub async fn run_monitor(cfg: &AppConfig, watch_dir: &Path) -> Result<()> {
    let client = Client::new();
    let (tx, mut rx) = mpsc::unbounded_channel::<Event>();
    let window = Arc::new(Mutex::new(RateWindow::new()));
    let watch_dir_buf = watch_dir.to_path_buf();

    // Spawn watcher thread
    let tx_clone = tx.clone();
    std::thread::spawn(move || {
        let mut watcher: RecommendedWatcher = recommended_watcher(move |res| {
            if let Ok(event) = res { let _ = tx_clone.send(event); }
        }).expect("watcher");
        watcher.watch(&watch_dir_buf, RecursiveMode::Recursive).expect("watch path");
        // Block forever
        loop { std::thread::sleep(Duration::from_secs(60)); }
    });

    println!("Monitoring {}...", watch_dir.display());
    let mut last_ai = Instant::now();
    let mut last_action: Option<String> = None;

    while let Some(event) = rx.recv().await {
        let now = Instant::now();
        if matches!(event.kind, EventKind::Modify(_) | EventKind::Create(_)) {
            if let Ok(mut rw) = window.lock() { rw.push(now); }
        }

        if now.duration_since(last_ai) >= Duration::from_millis(500) {
            let rate = if let Ok(mut rw) = window.lock() { rw.per_second(now) } else { 0.0 };
            let features = Features {
                file_write_rate_per_sec: rate,
                unique_ext_ratio: 0.0,
                entropy_delta: 0.0,
                process_count_delta: 0.0,
            };
            match query_ai(&client, &cfg.ai_url, &features).await {
                Ok(AiResponse { risk_score, action }) => {
                    if last_action.as_deref() != Some(&action) {
                        println!("AI: risk={:.2} action={}", risk_score, action);
                        last_action = Some(action);
                    }
                }
                Err(e) => {
                    eprintln!("AI query failed: {}", e);
                }
            }
            last_ai = now;
        }
    }
    Ok(())
}

