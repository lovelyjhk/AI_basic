/*
 * Medical Cybersecurity System - Rust Defense Engine
 * 
 * AI 기반 선제적 랜섬웨어 방어 시스템
 * 핵심: 초고속 증분 백업 + 격리된 안전 쓰기
 * 석사 논문용 MVP (3개월 완성)
 */

use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, Instant, Duration, UNIX_EPOCH};
use std::fs::{self, File, Metadata};
use std::io::{self, Read, Write, BufReader, BufWriter};

use serde::{Deserialize, Serialize};
use anyhow::{Result, Context, bail};
use rayon::prelude::*;
use sha2::{Sha256, Digest};

// Python 바인딩 모듈
#[cfg(feature = "python")]
pub mod python_bindings;

// ==================== 데이터 구조체 ====================

/// 파일 변경 이벤트
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileChangeEvent {
    pub path: String,
    pub event_type: String,  // "created", "modified", "deleted"
    pub timestamp: u64,
    pub file_size: u64,
    pub file_hash: Option<String>,
}

/// 백업 결과
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupResult {
    pub success: bool,
    pub files_backed_up: usize,
    pub total_bytes: u64,
    pub duration_ms: u64,
    pub backup_path: String,
    pub error_message: Option<String>,
}

/// 모니터링 통계
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonitoringStats {
    pub files_modified_per_sec: f64,
    pub bytes_written_per_sec: f64,
    pub suspicious_processes: Vec<String>,
    pub total_files_monitored: usize,
    pub threat_score: f64,  // 0.0 ~ 1.0
}

/// 방어 액션 결과
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DefenseActionResult {
    pub action_type: String,  // "incremental_backup", "isolated_write", "block_process"
    pub success: bool,
    pub duration_ms: u64,
    pub protected_files: usize,
    pub error_message: Option<String>,
}

// ==================== 파일 모니터링 시스템 ====================

/// 파일 시스템 모니터
pub struct FileSystemMonitor {
    watch_paths: Vec<PathBuf>,
    file_states: Arc<Mutex<HashMap<PathBuf, FileState>>>,
    change_events: Arc<Mutex<Vec<FileChangeEvent>>>,
}

#[derive(Debug, Clone)]
struct FileState {
    last_modified: SystemTime,
    size: u64,
    hash: String,
}

impl FileSystemMonitor {
    pub fn new(watch_paths: Vec<PathBuf>) -> Self {
        Self {
            watch_paths,
            file_states: Arc::new(Mutex::new(HashMap::new())),
            change_events: Arc::new(Mutex::new(Vec::new())),
        }
    }

    /// 초기 파일 상태 스캔
    pub fn initial_scan(&self) -> Result<usize> {
        let mut count = 0;
        let mut states = self.file_states.lock().unwrap();
        
        for watch_path in &self.watch_paths {
            if !watch_path.exists() {
                continue;
            }
            
            let entries = walkdir::WalkDir::new(watch_path)
                .follow_links(false)
                .into_iter()
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().is_file());
            
            for entry in entries {
                let path = entry.path().to_path_buf();
                if let Ok(metadata) = fs::metadata(&path) {
                    if let Ok(modified) = metadata.modified() {
                        let hash = Self::calculate_file_hash(&path).unwrap_or_default();
                        states.insert(path, FileState {
                            last_modified: modified,
                            size: metadata.len(),
                            hash,
                        });
                        count += 1;
                    }
                }
            }
        }
        
        Ok(count)
    }

    /// 변경 사항 감지
    pub fn detect_changes(&self) -> Result<Vec<FileChangeEvent>> {
        let mut events = Vec::new();
        let mut states = self.file_states.lock().unwrap();
        
        for watch_path in &self.watch_paths {
            if !watch_path.exists() {
                continue;
            }
            
            let entries = walkdir::WalkDir::new(watch_path)
                .follow_links(false)
                .into_iter()
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().is_file());
            
            for entry in entries {
                let path = entry.path().to_path_buf();
                if let Ok(metadata) = fs::metadata(&path) {
                    if let Ok(modified) = metadata.modified() {
                        let current_hash = Self::calculate_file_hash(&path).unwrap_or_default();
                        
                        let event_type = if let Some(state) = states.get(&path) {
                            if state.hash != current_hash {
                                "modified"
                            } else {
                                continue;
                            }
                        } else {
                            "created"
                        };
                        
                        let event = FileChangeEvent {
                            path: path.to_string_lossy().to_string(),
                            event_type: event_type.to_string(),
                            timestamp: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
                            file_size: metadata.len(),
                            file_hash: Some(current_hash.clone()),
                        };
                        
                        events.push(event);
                        
                        states.insert(path, FileState {
                            last_modified: modified,
                            size: metadata.len(),
                            hash: current_hash,
                        });
                    }
                }
            }
        }
        
        Ok(events)
    }

    /// 모니터링 통계 생성
    pub fn get_monitoring_stats(&self, window_secs: u64) -> Result<MonitoringStats> {
        let events = self.change_events.lock().unwrap();
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
        
        let recent_events: Vec<_> = events.iter()
            .filter(|e| now - e.timestamp <= window_secs)
            .collect();
        
        let files_modified = recent_events.len();
        let total_bytes: u64 = recent_events.iter().map(|e| e.file_size).sum();
        
        let files_per_sec = files_modified as f64 / window_secs as f64;
        let bytes_per_sec = total_bytes as f64 / window_secs as f64;
        
        // 위협 점수 계산 (간단한 휴리스틱)
        let threat_score = if files_per_sec > 100.0 {
            0.9
        } else if files_per_sec > 50.0 {
            0.7
        } else if files_per_sec > 10.0 {
            0.5
        } else {
            0.1
        };
        
        Ok(MonitoringStats {
            files_modified_per_sec: files_per_sec,
            bytes_written_per_sec: bytes_per_sec,
            suspicious_processes: vec![],
            total_files_monitored: self.file_states.lock().unwrap().len(),
            threat_score,
        })
    }

    /// 파일 해시 계산
    fn calculate_file_hash(path: &Path) -> Result<String> {
        let mut file = File::open(path)?;
        let mut hasher = Sha256::new();
        let mut buffer = [0u8; 8192];
        
        loop {
            let n = file.read(&mut buffer)?;
            if n == 0 {
                break;
            }
            hasher.update(&buffer[..n]);
        }
        
        Ok(format!("{:x}", hasher.finalize()))
    }
}

// ==================== 초고속 증분 백업 시스템 ====================

/// 증분 백업 엔진
pub struct IncrementalBackupEngine {
    source_dir: PathBuf,
    backup_dir: PathBuf,
    last_backup_time: Arc<Mutex<Option<SystemTime>>>,
}

impl IncrementalBackupEngine {
    pub fn new(source_dir: PathBuf, backup_dir: PathBuf) -> Self {
        Self {
            source_dir,
            backup_dir,
            last_backup_time: Arc::new(Mutex::new(None)),
        }
    }

    /// 증분 백업 실행 (병렬 처리)
    pub fn execute_backup(&self) -> Result<BackupResult> {
        let start_time = Instant::now();
        
        // 백업 디렉토리 생성
        if !self.backup_dir.exists() {
            fs::create_dir_all(&self.backup_dir)?;
        }
        
        // 타임스탬프 기반 백업 폴더
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        let backup_path = self.backup_dir.join(format!("backup_{}", timestamp));
        fs::create_dir_all(&backup_path)?;
        
        // 변경된 파일 식별
        let last_backup = *self.last_backup_time.lock().unwrap();
        let files_to_backup: Vec<PathBuf> = walkdir::WalkDir::new(&self.source_dir)
            .follow_links(false)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .filter_map(|e| {
                let path = e.path().to_path_buf();
                if let Ok(metadata) = fs::metadata(&path) {
                    if let Ok(modified) = metadata.modified() {
                        if let Some(last_backup) = last_backup {
                            if modified > last_backup {
                                return Some(path);
                            }
                        } else {
                            return Some(path);
                        }
                    }
                }
                None
            })
            .collect();
        
        // 병렬 백업 실행 (rayon 사용)
        let total_bytes: u64 = files_to_backup
            .par_iter()
            .map(|source_file| {
                let relative_path = source_file.strip_prefix(&self.source_dir).unwrap();
                let dest_file = backup_path.join(relative_path);
                
                // 디렉토리 생성
                if let Some(parent) = dest_file.parent() {
                    let _ = fs::create_dir_all(parent);
                }
                
                // 파일 복사
                if let Ok(_) = fs::copy(source_file, &dest_file) {
                    fs::metadata(&dest_file).map(|m| m.len()).unwrap_or(0)
                } else {
                    0
                }
            })
            .sum();
        
        let duration = start_time.elapsed();
        
        // 마지막 백업 시간 업데이트
        *self.last_backup_time.lock().unwrap() = Some(SystemTime::now());
        
        Ok(BackupResult {
            success: true,
            files_backed_up: files_to_backup.len(),
            total_bytes,
            duration_ms: duration.as_millis() as u64,
            backup_path: backup_path.to_string_lossy().to_string(),
            error_message: None,
        })
    }

    /// 특정 파일들만 백업 (AI 예측 기반)
    pub fn backup_specific_files(&self, file_paths: &[PathBuf]) -> Result<BackupResult> {
        let start_time = Instant::now();
        
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        let backup_path = self.backup_dir.join(format!("emergency_backup_{}", timestamp));
        fs::create_dir_all(&backup_path)?;
        
        // 병렬 백업
        let total_bytes: u64 = file_paths
            .par_iter()
            .map(|source_file| {
                if let Ok(relative_path) = source_file.strip_prefix(&self.source_dir) {
                    let dest_file = backup_path.join(relative_path);
                    
                    if let Some(parent) = dest_file.parent() {
                        let _ = fs::create_dir_all(parent);
                    }
                    
                    if let Ok(_) = fs::copy(source_file, &dest_file) {
                        return fs::metadata(&dest_file).map(|m| m.len()).unwrap_or(0);
                    }
                }
                0
            })
            .sum();
        
        let duration = start_time.elapsed();
        
        Ok(BackupResult {
            success: true,
            files_backed_up: file_paths.len(),
            total_bytes,
            duration_ms: duration.as_millis() as u64,
            backup_path: backup_path.to_string_lossy().to_string(),
            error_message: None,
        })
    }
}

// ==================== 격리된 안전 쓰기 시스템 ====================

/// 격리된 쓰기 채널 관리자
pub struct IsolatedWriteManager {
    protected_dir: PathBuf,
    clean_log_dir: PathBuf,
    is_isolation_active: Arc<Mutex<bool>>,
    write_log: Arc<Mutex<Vec<WriteOperation>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WriteOperation {
    pub original_path: String,
    pub redirected_path: String,
    pub timestamp: u64,
    pub data_size: u64,
}

impl IsolatedWriteManager {
    pub fn new(protected_dir: PathBuf, clean_log_dir: PathBuf) -> Self {
        Self {
            protected_dir,
            clean_log_dir,
            is_isolation_active: Arc::new(Mutex::new(false)),
            write_log: Arc::new(Mutex::new(Vec::new())),
        }
    }

    /// 격리 모드 활성화
    pub fn activate_isolation(&self) -> Result<()> {
        *self.is_isolation_active.lock().unwrap() = true;
        
        // 클린 로그 디렉토리 생성
        if !self.clean_log_dir.exists() {
            fs::create_dir_all(&self.clean_log_dir)?;
        }
        
        Ok(())
    }

    /// 격리 모드 비활성화
    pub fn deactivate_isolation(&self) -> Result<()> {
        *self.is_isolation_active.lock().unwrap() = false;
        Ok(())
    }

    /// 쓰기 작업 리디렉션 (시뮬레이션)
    pub fn redirect_write(&self, original_path: &Path, data: &[u8]) -> Result<WriteOperation> {
        if !*self.is_isolation_active.lock().unwrap() {
            bail!("Isolation mode is not active");
        }
        
        // 상대 경로 계산
        let relative_path = original_path.strip_prefix(&self.protected_dir)
            .unwrap_or(original_path);
        
        // 리디렉트 경로 생성
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        let redirected_path = self.clean_log_dir
            .join(format!("{}_{}", timestamp, relative_path.to_string_lossy()));
        
        // 부모 디렉토리 생성
        if let Some(parent) = redirected_path.parent() {
            fs::create_dir_all(parent)?;
        }
        
        // 데이터 쓰기
        let mut file = File::create(&redirected_path)?;
        file.write_all(data)?;
        
        let operation = WriteOperation {
            original_path: original_path.to_string_lossy().to_string(),
            redirected_path: redirected_path.to_string_lossy().to_string(),
            timestamp,
            data_size: data.len() as u64,
        };
        
        self.write_log.lock().unwrap().push(operation.clone());
        
        Ok(operation)
    }

    /// 클린 로그를 주 서버로 동기화
    pub fn sync_clean_logs(&self) -> Result<usize> {
        let write_log = self.write_log.lock().unwrap();
        let mut synced_count = 0;
        
        for operation in write_log.iter() {
            let source = PathBuf::from(&operation.redirected_path);
            let dest = PathBuf::from(&operation.original_path);
            
            if source.exists() {
                if let Some(parent) = dest.parent() {
                    let _ = fs::create_dir_all(parent);
                }
                
                if fs::copy(&source, &dest).is_ok() {
                    synced_count += 1;
                }
            }
        }
        
        Ok(synced_count)
    }

    /// 쓰기 로그 조회
    pub fn get_write_log(&self) -> Vec<WriteOperation> {
        self.write_log.lock().unwrap().clone()
    }
}

// ==================== 통합 방어 시스템 ====================

/// 통합 방어 엔진
pub struct DefenseEngine {
    monitor: FileSystemMonitor,
    backup_engine: IncrementalBackupEngine,
    write_manager: IsolatedWriteManager,
}

impl DefenseEngine {
    pub fn new(
        watch_paths: Vec<PathBuf>,
        source_dir: PathBuf,
        backup_dir: PathBuf,
        clean_log_dir: PathBuf,
    ) -> Self {
        Self {
            monitor: FileSystemMonitor::new(watch_paths),
            backup_engine: IncrementalBackupEngine::new(source_dir.clone(), backup_dir),
            write_manager: IsolatedWriteManager::new(source_dir, clean_log_dir),
        }
    }

    /// 초기화
    pub fn initialize(&self) -> Result<usize> {
        self.monitor.initial_scan()
    }

    /// AI 예측에 기반한 방어 액션 실행
    pub fn execute_defense_action(&self, threat_score: f64) -> Result<DefenseActionResult> {
        let start_time = Instant::now();
        
        if threat_score > 0.7 {
            // 긴급 백업 + 격리 모드 활성화
            let backup_result = self.backup_engine.execute_backup()?;
            self.write_manager.activate_isolation()?;
            
            Ok(DefenseActionResult {
                action_type: "emergency_backup_and_isolation".to_string(),
                success: true,
                duration_ms: start_time.elapsed().as_millis() as u64,
                protected_files: backup_result.files_backed_up,
                error_message: None,
            })
        } else if threat_score > 0.4 {
            // 증분 백업만 실행
            let backup_result = self.backup_engine.execute_backup()?;
            
            Ok(DefenseActionResult {
                action_type: "incremental_backup".to_string(),
                success: true,
                duration_ms: start_time.elapsed().as_millis() as u64,
                protected_files: backup_result.files_backed_up,
                error_message: None,
            })
        } else {
            // 모니터링만 지속
            Ok(DefenseActionResult {
                action_type: "monitoring".to_string(),
                success: true,
                duration_ms: start_time.elapsed().as_millis() as u64,
                protected_files: 0,
                error_message: None,
            })
        }
    }

    /// 모니터링 통계 조회
    pub fn get_stats(&self) -> Result<MonitoringStats> {
        self.monitor.get_monitoring_stats(10)
    }

    /// 공격 종료 후 복구
    pub fn restore_normal_operations(&self) -> Result<usize> {
        self.write_manager.deactivate_isolation()?;
        self.write_manager.sync_clean_logs()
    }
}

// ==================== 벤치마크 유틸리티 ====================

/// 성능 벤치마크 실행
pub fn benchmark_defense_speed(
    source_dir: &Path,
    file_count: usize,
    file_size_kb: usize,
) -> Result<HashMap<String, u64>> {
    let mut results = HashMap::new();
    
    // 테스트 파일 생성
    let test_dir = source_dir.join("benchmark_test");
    fs::create_dir_all(&test_dir)?;
    
    let data = vec![0u8; file_size_kb * 1024];
    for i in 0..file_count {
        let file_path = test_dir.join(format!("test_file_{}.dat", i));
        let mut file = File::create(file_path)?;
        file.write_all(&data)?;
    }
    
    // 백업 속도 측정
    let backup_engine = IncrementalBackupEngine::new(
        test_dir.clone(),
        source_dir.join("benchmark_backup"),
    );
    
    let start = Instant::now();
    let backup_result = backup_engine.execute_backup()?;
    let backup_duration = start.elapsed().as_millis() as u64;
    
    results.insert("backup_duration_ms".to_string(), backup_duration);
    results.insert("files_backed_up".to_string(), backup_result.files_backed_up as u64);
    results.insert("throughput_mbps".to_string(), 
        (backup_result.total_bytes as f64 / 1024.0 / 1024.0) / (backup_duration as f64 / 1000.0) as u64);
    
    // 정리
    fs::remove_dir_all(&test_dir)?;
    
    Ok(results)
}

// ==================== 테스트 ====================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_backup_engine() {
        let temp_dir = std::env::temp_dir();
        let source_dir = temp_dir.join("test_source");
        let backup_dir = temp_dir.join("test_backup");
        
        fs::create_dir_all(&source_dir).unwrap();
        
        // 테스트 파일 생성
        let test_file = source_dir.join("test.txt");
        fs::write(&test_file, b"Hello, Medical Cybersecurity!").unwrap();
        
        let engine = IncrementalBackupEngine::new(source_dir.clone(), backup_dir.clone());
        let result = engine.execute_backup().unwrap();
        
        assert!(result.success);
        assert_eq!(result.files_backed_up, 1);
        
        // 정리
        fs::remove_dir_all(&source_dir).ok();
        fs::remove_dir_all(&backup_dir).ok();
    }

    #[test]
    fn test_isolated_write() {
        let temp_dir = std::env::temp_dir();
        let protected_dir = temp_dir.join("test_protected");
        let clean_log_dir = temp_dir.join("test_clean_log");
        
        fs::create_dir_all(&protected_dir).unwrap();
        
        let manager = IsolatedWriteManager::new(protected_dir.clone(), clean_log_dir.clone());
        manager.activate_isolation().unwrap();
        
        let test_path = protected_dir.join("test.txt");
        let operation = manager.redirect_write(&test_path, b"test data").unwrap();
        
        assert!(PathBuf::from(&operation.redirected_path).exists());
        
        // 정리
        fs::remove_dir_all(&protected_dir).ok();
        fs::remove_dir_all(&clean_log_dir).ok();
    }
}
