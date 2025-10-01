use crate::config::Config;
use crate::monitor::FileEvent;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, VecDeque};
use std::fs::File;
use std::io::Read;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThreatAlert {
    pub timestamp: DateTime<Utc>,
    pub score: u32,
    pub description: String,
    pub file_path: String,
    pub threat_type: String,
}

pub struct ThreatDetector {
    config: Config,
    event_window: VecDeque<FileEvent>,
    file_hashes: HashMap<PathBuf, String>,
    files_monitored: usize,
}

impl ThreatDetector {
    pub fn new(config: Config) -> Self {
        ThreatDetector {
            config,
            event_window: VecDeque::new(),
            file_hashes: HashMap::new(),
            files_monitored: 0,
        }
    }

    pub fn process_event(&mut self, event: &FileEvent) {
        // Add to event window
        self.event_window.push_back(event.clone());
        self.files_monitored += 1;

        // Remove old events outside time window
        let window_duration = chrono::Duration::seconds(self.config.detection.time_window_seconds as i64);
        let cutoff_time = Utc::now() - window_duration;
        
        while let Some(front) = self.event_window.front() {
            if front.timestamp < cutoff_time {
                self.event_window.pop_front();
            } else {
                break;
            }
        }
    }

    pub fn check_threat(&self) -> Option<ThreatAlert> {
        let mut threat_score = 0u32;
        let mut threat_reasons = Vec::new();

        // Check 1: Rapid file changes
        let recent_events = self.event_window.len();
        if recent_events > self.config.detection.rapid_change_threshold {
            threat_score += 30;
            threat_reasons.push(format!("Rapid file changes detected: {} files/min", recent_events));
        }

        // Check 2: Suspicious file extensions
        let suspicious_count = self.event_window.iter()
            .filter(|e| {
                if let Some(ext) = e.path.extension() {
                    let ext_str = format!(".{}", ext.to_string_lossy());
                    self.config.detection.suspicious_extensions.contains(&ext_str)
                } else {
                    false
                }
            })
            .count();

        if suspicious_count > 0 {
            threat_score += 20;
            threat_reasons.push(format!("Suspicious extensions: {} files", suspicious_count));
        }

        // Check 3: Entropy analysis
        if let Some(last_event) = self.event_window.back() {
            if last_event.path.exists() {
                if let Ok(entropy) = calculate_entropy(&last_event.path) {
                    if entropy > self.config.detection.entropy_threshold {
                        threat_score += 40;
                        threat_reasons.push(format!("High entropy detected: {:.2} bits/byte", entropy));
                    }
                }
            }
        }

        // Check 4: Mass file renaming
        let rename_patterns = self.detect_mass_rename();
        if rename_patterns > 5 {
            threat_score += 10;
            threat_reasons.push(format!("Mass file renaming: {} patterns", rename_patterns));
        }

        // Generate alert if threat score exceeds threshold
        if threat_score >= 70 {
            let last_event = self.event_window.back()?;
            Some(ThreatAlert {
                timestamp: Utc::now(),
                score: threat_score,
                description: threat_reasons.join("; "),
                file_path: last_event.path.to_string_lossy().to_string(),
                threat_type: "Ransomware".to_string(),
            })
        } else {
            None
        }
    }

    fn detect_mass_rename(&self) -> usize {
        // Simple heuristic: count files with similar naming patterns
        let mut extension_changes = HashMap::new();
        
        for event in &self.event_window {
            if let Some(ext) = event.path.extension() {
                *extension_changes.entry(ext.to_string_lossy().to_string()).or_insert(0) += 1;
            }
        }

        extension_changes.values().filter(|&&count| count > 3).count()
    }

    pub fn files_monitored(&self) -> usize {
        self.files_monitored
    }
}

fn calculate_entropy(path: &PathBuf) -> Result<f64, std::io::Error> {
    let mut file = File::open(path)?;
    let mut buffer = vec![0u8; 8192]; // Read first 8KB for performance
    let bytes_read = file.read(&mut buffer)?;
    
    if bytes_read == 0 {
        return Ok(0.0);
    }

    // Calculate byte frequency
    let mut frequency = [0u32; 256];
    for &byte in &buffer[..bytes_read] {
        frequency[byte as usize] += 1;
    }

    // Calculate Shannon entropy
    let mut entropy = 0.0;
    let total = bytes_read as f64;
    
    for &count in &frequency {
        if count > 0 {
            let p = count as f64 / total;
            entropy -= p * p.log2();
        }
    }

    Ok(entropy)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn test_entropy_calculation() {
        // Create a file with random data (high entropy)
        let mut file = NamedTempFile::new().unwrap();
        let random_data: Vec<u8> = (0..1000).map(|_| rand::random::<u8>()).collect();
        file.write_all(&random_data).unwrap();
        
        let entropy = calculate_entropy(&file.path().to_path_buf()).unwrap();
        assert!(entropy > 7.0, "Random data should have high entropy");
    }

    #[test]
    fn test_low_entropy() {
        // Create a file with repeated data (low entropy)
        let mut file = NamedTempFile::new().unwrap();
        file.write_all(&vec![b'A'; 1000]).unwrap();
        
        let entropy = calculate_entropy(&file.path().to_path_buf()).unwrap();
        assert!(entropy < 1.0, "Repeated data should have low entropy");
    }
}
