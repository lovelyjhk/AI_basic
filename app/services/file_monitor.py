"""
Real-time File Monitoring System
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime
import hashlib
import json
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent, FileMovedEvent
from watchdog.utils import stat

from app.core.config import settings
from app.services.rl_agent import threat_analyzer
from app.services.crypto_engine import get_crypto_engine

logger = logging.getLogger(__name__)


class FileMonitorHandler(FileSystemEventHandler):
    """파일 시스템 이벤트 핸들러"""
    
    def __init__(self, monitor_service):
        self.monitor_service = monitor_service
        self.processed_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}
    
    def on_created(self, event):
        """파일 생성 이벤트"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "created")
    
    def on_modified(self, event):
        """파일 수정 이벤트"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "modified")
    
    def on_deleted(self, event):
        """파일 삭제 이벤트"""
        if not event.is_directory:
            self._handle_file_event(event.src_path, "deleted")
    
    def on_moved(self, event):
        """파일 이동 이벤트"""
        if not event.is_directory:
            self._handle_file_event(event.dest_path, "moved", old_path=event.src_path)
    
    def _handle_file_event(self, file_path: str, event_type: str, old_path: str = None):
        """파일 이벤트 처리"""
        try:
            # 파일 확장자 확인
            if not self._is_monitored_file(file_path):
                return
            
            # 중복 처리 방지
            if file_path in self.processed_files:
                return
            
            self.processed_files.add(file_path)
            
            # 이벤트 정보 생성
            event_info = {
                "file_path": file_path,
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "old_path": old_path,
                "file_size": self._get_file_size(file_path),
                "file_hash": self._calculate_file_hash(file_path) if event_type != "deleted" else None
            }
            
            # 이벤트 처리
            asyncio.create_task(self.monitor_service.process_file_event(event_info))
            
            logger.info(f"File event processed: {event_type} - {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to handle file event {file_path}: {e}")
    
    def _is_monitored_file(self, file_path: str) -> bool:
        """모니터링 대상 파일인지 확인"""
        path = Path(file_path)
        
        # 확장자 확인
        if path.suffix.lower() not in settings.MONITOR_FILE_EXTENSIONS:
            return False
        
        # 파일 크기 확인
        try:
            file_size = path.stat().st_size
            if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                return False
        except OSError:
            return False
        
        return True
    
    def _get_file_size(self, file_path: str) -> int:
        """파일 크기 조회"""
        try:
            return Path(file_path).stat().st_size
        except OSError:
            return 0
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception:
            return ""


class FileMonitorService:
    """파일 모니터링 서비스"""
    
    def __init__(self):
        self.observer = None
        self.handler = None
        self.is_running = False
        self.monitored_directories: Set[str] = set()
        self.event_callbacks: List[Callable] = []
        self.crypto_engine = get_crypto_engine()
        
        # 통계
        self.stats = {
            "files_processed": 0,
            "threats_detected": 0,
            "files_encrypted": 0,
            "events_processed": 0,
            "start_time": None
        }
    
    async def start_monitoring(self):
        """파일 모니터링 시작"""
        try:
            logger.info("Starting file monitoring service...")
            
            # 모니터링 디렉토리 확인 및 생성
            for directory in settings.MONITOR_DIRECTORIES:
                dir_path = Path(directory)
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created monitoring directory: {directory}")
                
                self.monitored_directories.add(str(dir_path.absolute()))
            
            # 이벤트 핸들러 생성
            self.handler = FileMonitorHandler(self)
            
            # 옵저버 생성 및 시작
            self.observer = Observer()
            
            for directory in self.monitored_directories:
                self.observer.schedule(self.handler, directory, recursive=True)
                logger.info(f"Monitoring directory: {directory}")
            
            self.observer.start()
            self.is_running = True
            self.stats["start_time"] = datetime.utcnow()
            
            logger.info("File monitoring service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")
            raise
    
    async def stop_monitoring(self):
        """파일 모니터링 중지"""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
            
            self.is_running = False
            logger.info("File monitoring service stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop file monitoring: {e}")
    
    async def process_file_event(self, event_info: Dict[str, Any]):
        """파일 이벤트 처리"""
        try:
            self.stats["events_processed"] += 1
            
            # 파일 생성/수정 이벤트인 경우 위협 분석
            if event_info["event_type"] in ["created", "modified"]:
                await self._analyze_file_threat(event_info)
            
            # 콜백 함수 실행
            for callback in self.event_callbacks:
                try:
                    await callback(event_info)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            logger.debug(f"Processed file event: {event_info['event_type']} - {event_info['file_path']}")
            
        except Exception as e:
            logger.error(f"Failed to process file event: {e}")
    
    async def _analyze_file_threat(self, event_info: Dict[str, Any]):
        """파일 위협 분석"""
        try:
            file_path = event_info["file_path"]
            file_hash = event_info.get("file_hash")
            
            # RL 에이전트를 통한 위협 분석
            analysis_result = threat_analyzer.analyze_file(file_path, file_hash)
            
            if analysis_result.get("threat_detected", False):
                self.stats["threats_detected"] += 1
                
                # 위협 탐지 로그
                threat_info = {
                    "file_path": file_path,
                    "file_hash": file_hash,
                    "threat_detected": True,
                    "confidence": analysis_result.get("confidence", 0.0),
                    "threat_level": analysis_result.get("threat_level", "unknown"),
                    "indicators": analysis_result.get("indicators", []),
                    "detected_at": datetime.utcnow().isoformat(),
                    "analysis_method": analysis_result.get("analysis_method", "unknown")
                }
                
                logger.warning(f"Threat detected in file: {file_path}")
                logger.warning(f"Threat info: {json.dumps(threat_info, indent=2)}")
                
                # 위협 대응 조치
                await self._handle_threat_response(threat_info)
            
            self.stats["files_processed"] += 1
            
        except Exception as e:
            logger.error(f"Failed to analyze file threat: {e}")
    
    async def _handle_threat_response(self, threat_info: Dict[str, Any]):
        """위협 대응 조치"""
        try:
            file_path = threat_info["file_path"]
            threat_level = threat_info.get("threat_level", "low")
            
            if threat_level in ["high", "critical"]:
                # 고위험 파일 격리
                await self._quarantine_file(file_path)
                
                # 파일 암호화
                await self._encrypt_sensitive_file(file_path)
                
                logger.warning(f"High-risk file quarantined and encrypted: {file_path}")
            
            elif threat_level == "medium":
                # 중위험 파일 암호화
                await self._encrypt_sensitive_file(file_path)
                
                logger.info(f"Medium-risk file encrypted: {file_path}")
            
            # TODO: 데이터베이스에 위협 정보 저장
            # TODO: 관리자에게 알림 전송
            
        except Exception as e:
            logger.error(f"Failed to handle threat response: {e}")
    
    async def _quarantine_file(self, file_path: str):
        """파일 격리"""
        try:
            quarantine_dir = Path("/app/quarantine")
            quarantine_dir.mkdir(exist_ok=True)
            
            file_name = Path(file_path).name
            quarantine_path = quarantine_dir / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file_name}"
            
            # 파일 이동
            import shutil
            shutil.move(file_path, quarantine_path)
            
            logger.info(f"File quarantined: {file_path} -> {quarantine_path}")
            
        except Exception as e:
            logger.error(f"Failed to quarantine file {file_path}: {e}")
    
    async def _encrypt_sensitive_file(self, file_path: str):
        """민감한 파일 암호화"""
        try:
            # 암호화 키 생성
            key_id = f"auto_encrypt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            key_info = self.crypto_engine.create_key(key_id)
            
            # 암호화된 파일 경로
            encrypted_path = f"{file_path}.encrypted"
            
            # 파일 암호화
            encrypt_result = self.crypto_engine.encrypt_file(file_path, encrypted_path, key_id)
            
            if encrypt_result.get("success", False):
                self.stats["files_encrypted"] += 1
                logger.info(f"File encrypted: {file_path} -> {encrypted_path}")
                
                # 원본 파일 삭제 (선택사항)
                # os.remove(file_path)
            else:
                logger.error(f"Failed to encrypt file: {encrypt_result.get('error_message')}")
            
        except Exception as e:
            logger.error(f"Failed to encrypt sensitive file {file_path}: {e}")
    
    def add_event_callback(self, callback: Callable):
        """이벤트 콜백 추가"""
        self.event_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """모니터링 통계 조회"""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
        
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "is_running": self.is_running,
            "monitored_directories": list(self.monitored_directories)
        }
    
    async def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """디렉토리 스캔"""
        try:
            scan_results = []
            directory_path = Path(directory)
            
            if not directory_path.exists():
                return scan_results
            
            for file_path in directory_path.rglob("*"):
                if file_path.is_file() and self.handler._is_monitored_file(str(file_path)):
                    file_info = {
                        "file_path": str(file_path),
                        "file_size": file_path.stat().st_size,
                        "file_hash": self.handler._calculate_file_hash(str(file_path)),
                        "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "scanned_at": datetime.utcnow().isoformat()
                    }
                    scan_results.append(file_info)
            
            logger.info(f"Scanned directory {directory}: {len(scan_results)} files found")
            return scan_results
            
        except Exception as e:
            logger.error(f"Failed to scan directory {directory}: {e}")
            return []


# 전역 파일 모니터링 서비스 인스턴스
file_monitor_service = None


def get_file_monitor_service() -> FileMonitorService:
    """파일 모니터링 서비스 인스턴스 반환"""
    global file_monitor_service
    if file_monitor_service is None:
        file_monitor_service = FileMonitorService()
    return file_monitor_service


async def start_file_monitoring():
    """파일 모니터링 시작"""
    service = get_file_monitor_service()
    await service.start_monitoring()


async def stop_file_monitoring():
    """파일 모니터링 중지"""
    service = get_file_monitor_service()
    await service.stop_monitoring()


if __name__ == "__main__":
    # 파일 모니터링 서비스 테스트
    async def main():
        service = FileMonitorService()
        
        # 이벤트 콜백 추가
        async def event_callback(event_info):
            print(f"File event: {event_info}")
        
        service.add_event_callback(event_callback)
        
        # 모니터링 시작
        await service.start_monitoring()
        
        try:
            # 60초 동안 모니터링
            await asyncio.sleep(60)
        finally:
            # 모니터링 중지
            await service.stop_monitoring()
            
            # 통계 출력
            stats = service.get_statistics()
            print(f"Monitoring statistics: {json.dumps(stats, indent=2)}")
    
    asyncio.run(main())