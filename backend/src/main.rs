use anyhow::Result;
use axum::{
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Json},
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;
use tower_http::cors::CorsLayer;
use tracing::{info, warn};
use tracing_subscriber;

mod backup;
mod config;
mod crypto;
mod detector;
mod monitor;
mod storage;

use crate::config::Config;
use crate::detector::{ThreatAlert, ThreatDetector};
use crate::monitor::FileMonitor;
use crate::storage::Storage;

#[derive(Clone)]
struct AppState {
    detector: Arc<RwLock<ThreatDetector>>,
    storage: Arc<Storage>,
    alerts: Arc<RwLock<Vec<ThreatAlert>>>,
    config: Arc<Config>,
}

#[derive(Serialize)]
struct StatusResponse {
    status: String,
    files_monitored: usize,
    threats_detected: usize,
    backups_count: usize,
    cpu_usage: f32,
    memory_usage: u64,
}

#[derive(Serialize)]
struct AlertResponse {
    alerts: Vec<ThreatAlert>,
}

#[derive(Deserialize)]
struct RestoreRequest {
    file_path: String,
    version: Option<u64>,
}

#[derive(Serialize)]
struct RestoreResponse {
    success: bool,
    message: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter("medguard=debug,info")
        .init();

    info!("🏥 MedGuard - Medical Ransomware Defense System");
    info!("Starting initialization...");

    // Load configuration
    let config = Config::load("config.toml").unwrap_or_else(|_| {
        warn!("Config file not found, using defaults");
        Config::default()
    });
    info!("✓ Configuration loaded");

    // Initialize storage
    let storage = Arc::new(Storage::new(&config.backup.storage_path)?);
    info!("✓ Storage initialized: {}", config.backup.storage_path);

    // Initialize threat detector
    let detector = Arc::new(RwLock::new(ThreatDetector::new(config.clone())));
    info!("✓ Threat detector initialized");

    // Initialize alert storage
    let alerts = Arc::new(RwLock::new(Vec::<ThreatAlert>::new()));

    // Create application state
    let state = AppState {
        detector: detector.clone(),
        storage: storage.clone(),
        alerts: alerts.clone(),
        config: Arc::new(config.clone()),
    };

    // Start file monitoring
    let monitor_state = state.clone();
    tokio::spawn(async move {
        if let Err(e) = start_monitoring(monitor_state).await {
            warn!("Monitoring error: {}", e);
        }
    });

    info!("✓ File monitoring started for {} paths", config.monitoring.watch_paths.len());

    // Build REST API
    let app = Router::new()
        .route("/api/status", get(get_status))
        .route("/api/alerts", get(get_alerts))
        .route("/api/backups", get(get_backups))
        .route("/api/restore", post(restore_file))
        .route("/api/metrics", get(get_metrics))
        .layer(CorsLayer::permissive())
        .with_state(state);

    // Start server
    let addr = "0.0.0.0:8080";
    info!("✓ Starting server on {}", addr);
    info!("🚀 MedGuard is ready!");
    info!("   Dashboard: http://localhost:3000");
    info!("   API: http://localhost:8080/api/status");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

async fn start_monitoring(state: AppState) -> Result<()> {
    let config = state.config.clone();
    let detector = state.detector.clone();
    let storage = state.storage.clone();
    let alerts = state.alerts.clone();

    let mut monitor = FileMonitor::new((*config).clone())?;

    while let Some(event) = monitor.next_event().await {
        // Analyze event for threats
        let mut detector_guard = detector.write().await;
        detector_guard.process_event(&event);

        if let Some(threat) = detector_guard.check_threat() {
            warn!("🚨 THREAT DETECTED: Score {} - {}", threat.score, threat.description);
            
            // Store alert
            let mut alerts_guard = alerts.write().await;
            alerts_guard.push(threat.clone());
            
            // Keep only last 1000 alerts
            if alerts_guard.len() > 1000 {
                alerts_guard.drain(0..100);
            }
        }

        // Perform incremental backup
        if event.path.exists() {
            if let Err(e) = storage.backup_file(&event.path).await {
                warn!("Backup failed for {:?}: {}", event.path, e);
            }
        }
    }

    Ok(())
}

async fn get_status(State(state): State<AppState>) -> impl IntoResponse {
    let mut sys = sysinfo::System::new_all();
    sys.refresh_all();

    let detector = state.detector.read().await;
    let alerts = state.alerts.read().await;
    
    let cpu_usage = sys.global_cpu_info().cpu_usage();
    let memory_usage = sys.used_memory();

    let response = StatusResponse {
        status: "active".to_string(),
        files_monitored: detector.files_monitored(),
        threats_detected: alerts.len(),
        backups_count: state.storage.backup_count().await.unwrap_or(0),
        cpu_usage,
        memory_usage,
    };

    Json(response)
}

async fn get_alerts(State(state): State<AppState>) -> impl IntoResponse {
    let alerts = state.alerts.read().await;
    let recent_alerts: Vec<ThreatAlert> = alerts.iter().rev().take(50).cloned().collect();
    
    Json(AlertResponse {
        alerts: recent_alerts,
    })
}

async fn get_backups(State(state): State<AppState>) -> impl IntoResponse {
    match state.storage.list_backups().await {
        Ok(backups) => (StatusCode::OK, Json(serde_json::json!({ "backups": backups }))),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!({ "error": e.to_string() })),
        ),
    }
}

async fn restore_file(
    State(state): State<AppState>,
    Json(req): Json<RestoreRequest>,
) -> impl IntoResponse {
    match state.storage.restore_file(&req.file_path, req.version).await {
        Ok(()) => Json(RestoreResponse {
            success: true,
            message: format!("File restored successfully: {}", req.file_path),
        }),
        Err(e) => Json(RestoreResponse {
            success: false,
            message: format!("Restoration failed: {}", e),
        }),
    }
}

async fn get_metrics(State(state): State<AppState>) -> impl IntoResponse {
    let detector = state.detector.read().await;
    let alerts = state.alerts.read().await;
    let backups = state.storage.backup_count().await.unwrap_or(0);

    let metrics = format!(
        "# HELP medguard_files_monitored Total number of files being monitored\n\
         # TYPE medguard_files_monitored gauge\n\
         medguard_files_monitored {}\n\
         # HELP medguard_threats_detected Total number of threats detected\n\
         # TYPE medguard_threats_detected counter\n\
         medguard_threats_detected {}\n\
         # HELP medguard_backups_total Total number of backup versions\n\
         # TYPE medguard_backups_total counter\n\
         medguard_backups_total {}\n",
        detector.files_monitored(),
        alerts.len(),
        backups
    );

    (StatusCode::OK, metrics)
}
