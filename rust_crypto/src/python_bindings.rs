/*
 * Python 바인딩 (PyO3)
 * Python AI 예측부와 Rust 실행부 연동
 */

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::path::PathBuf;
use std::collections::HashMap;

use crate::{
    DefenseEngine, BackupResult, MonitoringStats, DefenseActionResult,
    FileChangeEvent, WriteOperation, benchmark_defense_speed,
};

/// Python 노출용 DefenseEngine 래퍼
#[pyclass]
pub struct PyDefenseEngine {
    engine: DefenseEngine,
}

#[pymethods]
impl PyDefenseEngine {
    #[new]
    pub fn new(
        watch_paths: Vec<String>,
        source_dir: String,
        backup_dir: String,
        clean_log_dir: String,
    ) -> PyResult<Self> {
        let watch_paths: Vec<PathBuf> = watch_paths.iter().map(PathBuf::from).collect();
        let engine = DefenseEngine::new(
            watch_paths,
            PathBuf::from(source_dir),
            PathBuf::from(backup_dir),
            PathBuf::from(clean_log_dir),
        );
        
        Ok(Self { engine })
    }

    /// 초기화
    pub fn initialize(&self) -> PyResult<usize> {
        self.engine.initialize()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    /// 방어 액션 실행 (AI 예측 기반)
    pub fn execute_defense(&self, threat_score: f64) -> PyResult<PyObject> {
        let result = self.engine.execute_defense_action(threat_score)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            dict.set_item("action_type", result.action_type)?;
            dict.set_item("success", result.success)?;
            dict.set_item("duration_ms", result.duration_ms)?;
            dict.set_item("protected_files", result.protected_files)?;
            dict.set_item("error_message", result.error_message)?;
            Ok(dict.into())
        })
    }

    /// 모니터링 통계 조회
    pub fn get_monitoring_stats(&self) -> PyResult<PyObject> {
        let stats = self.engine.get_stats()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            dict.set_item("files_modified_per_sec", stats.files_modified_per_sec)?;
            dict.set_item("bytes_written_per_sec", stats.bytes_written_per_sec)?;
            dict.set_item("suspicious_processes", stats.suspicious_processes)?;
            dict.set_item("total_files_monitored", stats.total_files_monitored)?;
            dict.set_item("threat_score", stats.threat_score)?;
            Ok(dict.into())
        })
    }

    /// 정상 운영 복구
    pub fn restore_normal_operations(&self) -> PyResult<usize> {
        self.engine.restore_normal_operations()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }
}

/// 벤치마크 함수 (Python 노출)
#[pyfunction]
pub fn py_benchmark_defense(
    source_dir: String,
    file_count: usize,
    file_size_kb: usize,
) -> PyResult<PyObject> {
    let results = benchmark_defense_speed(
        &PathBuf::from(source_dir),
        file_count,
        file_size_kb,
    ).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    
    Python::with_gil(|py| {
        let dict = PyDict::new(py);
        for (key, value) in results {
            dict.set_item(key, value)?;
        }
        Ok(dict.into())
    })
}

/// Python 모듈 정의
#[pymodule]
fn medical_defense(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyDefenseEngine>()?;
    m.add_function(wrap_pyfunction!(py_benchmark_defense, m)?)?;
    Ok(())
}
