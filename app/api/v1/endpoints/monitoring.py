"""
Real-time monitoring endpoints with WebSocket support
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import asyncio
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.file_monitor import get_file_monitor_service
from app.services.rl_agent import threat_analyzer

router = APIRouter()

# WebSocket 연결 관리
class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.monitor_connections: List[WebSocket] = []
        self.alert_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket, connection_type: str = "general"):
        """WebSocket 연결"""
        await websocket.accept()
        
        if connection_type == "monitor":
            self.monitor_connections.append(websocket)
        elif connection_type == "alert":
            self.alert_connections.append(websocket)
        else:
            self.active_connections.append(websocket)
        
        logging.info(f"WebSocket connected: {connection_type}")
    
    def disconnect(self, websocket: WebSocket, connection_type: str = "general"):
        """WebSocket 연결 해제"""
        if connection_type == "monitor" and websocket in self.monitor_connections:
            self.monitor_connections.remove(websocket)
        elif connection_type == "alert" and websocket in self.alert_connections:
            self.alert_connections.remove(websocket)
        elif websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        logging.info(f"WebSocket disconnected: {connection_type}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """개인 메시지 전송"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logging.error(f"Failed to send personal message: {e}")
    
    async def broadcast(self, message: str, connection_type: str = "general"):
        """브로드캐스트 메시지 전송"""
        connections = []
        
        if connection_type == "monitor":
            connections = self.monitor_connections
        elif connection_type == "alert":
            connections = self.alert_connections
        else:
            connections = self.active_connections
        
        disconnected = []
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logging.error(f"Failed to send broadcast message: {e}")
                disconnected.append(connection)
        
        # 연결 해제된 소켓 제거
        for connection in disconnected:
            self.disconnect(connection, connection_type)
    
    async def send_monitoring_data(self, data: Dict[str, Any]):
        """모니터링 데이터 전송"""
        message = json.dumps({
            "type": "monitoring_data",
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })
        await self.broadcast(message, "monitor")
    
    async def send_alert(self, alert_data: Dict[str, Any]):
        """보안 알림 전송"""
        message = json.dumps({
            "type": "security_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "alert": alert_data
        })
        await self.broadcast(message, "alert")


# 전역 연결 관리자
manager = ConnectionManager()


@router.get("/dashboard")
async def monitoring_dashboard():
    """모니터링 대시보드 HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Medical Cybersecurity Monitoring Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .stat-card { background: #ecf0f1; padding: 20px; border-radius: 5px; text-align: center; }
            .stat-value { font-size: 2em; font-weight: bold; color: #2c3e50; }
            .stat-label { color: #7f8c8d; margin-top: 5px; }
            .logs { background: #2c3e50; color: #ecf0f1; padding: 20px; border-radius: 5px; height: 400px; overflow-y: auto; }
            .log-entry { margin: 5px 0; padding: 5px; border-left: 3px solid #3498db; }
            .alert { border-left-color: #e74c3c; }
            .warning { border-left-color: #f39c12; }
            .info { border-left-color: #3498db; }
            .success { border-left-color: #27ae60; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Medical Cybersecurity Monitoring Dashboard</h1>
                <p>Real-time threat detection and file monitoring</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" id="files-processed">0</div>
                    <div class="stat-label">Files Processed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="threats-detected">0</div>
                    <div class="stat-label">Threats Detected</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="files-encrypted">0</div>
                    <div class="stat-label">Files Encrypted</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="uptime">0s</div>
                    <div class="stat-label">Uptime</div>
                </div>
            </div>
            
            <div class="logs" id="logs">
                <div class="log-entry info">Monitoring dashboard initialized</div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket("ws://localhost:8000/api/v1/monitoring/ws/monitor");
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === "monitoring_data") {
                    updateStats(data.data);
                } else if (data.type === "security_alert") {
                    addLogEntry(data.alert, "alert");
                }
            };
            
            function updateStats(stats) {
                document.getElementById("files-processed").textContent = stats.files_processed || 0;
                document.getElementById("threats-detected").textContent = stats.threats_detected || 0;
                document.getElementById("files-encrypted").textContent = stats.files_encrypted || 0;
                document.getElementById("uptime").textContent = Math.round(stats.uptime_seconds || 0) + "s";
            }
            
            function addLogEntry(message, type = "info") {
                const logs = document.getElementById("logs");
                const entry = document.createElement("div");
                entry.className = `log-entry ${type}`;
                entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                logs.appendChild(entry);
                logs.scrollTop = logs.scrollHeight;
            }
            
            // 주기적으로 통계 업데이트
            setInterval(() => {
                fetch("/api/v1/monitoring/statistics")
                    .then(response => response.json())
                    .then(data => updateStats(data))
                    .catch(error => console.error("Failed to fetch statistics:", error));
            }, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """실시간 모니터링 WebSocket"""
    await manager.connect(websocket, "monitor")
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (선택사항)
            data = await websocket.receive_text()
            
            # 메시지 처리
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}),
                        websocket
                    )
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, "monitor")
        logging.info("Monitor WebSocket disconnected")


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """보안 알림 WebSocket"""
    await manager.connect(websocket, "alert")
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (선택사항)
            data = await websocket.receive_text()
            
            # 메시지 처리
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}),
                        websocket
                    )
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, "alert")
        logging.info("Alert WebSocket disconnected")


@router.get("/statistics")
async def get_monitoring_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """모니터링 통계 조회"""
    try:
        # 파일 모니터링 서비스 통계
        monitor_service = get_file_monitor_service()
        monitor_stats = monitor_service.get_statistics()
        
        # RL 에이전트 통계
        rl_stats = {
            "model_loaded": threat_analyzer.is_trained,
            "model_path": threat_analyzer.model_path
        }
        
        # 전체 통계
        statistics = {
            "monitoring": monitor_stats,
            "rl_agent": rl_stats,
            "websocket_connections": {
                "total": len(manager.active_connections),
                "monitor": len(manager.monitor_connections),
                "alert": len(manager.alert_connections)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return statistics
        
    except Exception as e:
        logging.error(f"Failed to get monitoring statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monitoring statistics"
        )


@router.get("/threats/recent")
async def get_recent_threats(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """최근 탐지된 위협 목록"""
    try:
        # TODO: 데이터베이스에서 최근 위협 조회
        # 임시 데이터
        recent_threats = [
            {
                "id": 1,
                "threat_type": "malware",
                "severity": "high",
                "file_path": "/monitor/suspicious_file.exe",
                "detected_at": datetime.utcnow().isoformat(),
                "confidence": 0.95
            }
        ]
        
        return recent_threats[:limit]
        
    except Exception as e:
        logging.error(f"Failed to get recent threats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent threats"
        )


@router.post("/scan/directory")
async def scan_directory(
    directory: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """디렉토리 스캔 실행"""
    try:
        monitor_service = get_file_monitor_service()
        scan_results = await monitor_service.scan_directory(directory)
        
        return {
            "directory": directory,
            "files_found": len(scan_results),
            "scan_results": scan_results,
            "scanned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Failed to scan directory {directory}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan directory: {e}"
        )


@router.get("/health")
async def monitoring_health() -> Dict[str, Any]:
    """모니터링 서비스 헬스 체크"""
    try:
        monitor_service = get_file_monitor_service()
        stats = monitor_service.get_statistics()
        
        return {
            "status": "healthy" if stats["is_running"] else "unhealthy",
            "monitoring_active": stats["is_running"],
            "uptime_seconds": stats.get("uptime_seconds", 0),
            "files_processed": stats.get("files_processed", 0),
            "threats_detected": stats.get("threats_detected", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# 백그라운드 작업: 주기적으로 모니터링 데이터 전송
async def broadcast_monitoring_data():
    """주기적으로 모니터링 데이터 브로드캐스트"""
    while True:
        try:
            if manager.monitor_connections:
                monitor_service = get_file_monitor_service()
                stats = monitor_service.get_statistics()
                
                await manager.send_monitoring_data(stats)
            
            await asyncio.sleep(5)  # 5초마다 업데이트
            
        except Exception as e:
            logging.error(f"Failed to broadcast monitoring data: {e}")
            await asyncio.sleep(10)  # 오류 시 10초 대기


# 백그라운드 작업 시작
async def start_monitoring_broadcast():
    """모니터링 브로드캐스트 시작"""
    asyncio.create_task(broadcast_monitoring_data())