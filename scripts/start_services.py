#!/usr/bin/env python3
"""
Medical Cybersecurity System - Service Startup Script
"""

import asyncio
import subprocess
import sys
import time
import signal
import os
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 서비스 프로세스들
processes = []


def signal_handler(signum, frame):
    """시그널 핸들러 - 서비스 종료"""
    logger.info("Received shutdown signal, stopping services...")
    
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        except Exception as e:
            logger.error(f"Error stopping process: {e}")
    
    sys.exit(0)


def start_fastapi_server():
    """FastAPI 서버 시작"""
    logger.info("Starting FastAPI server...")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    process = subprocess.Popen(cmd)
    processes.append(process)
    return process


def start_rl_agent():
    """RL 에이전트 서비스 시작"""
    logger.info("Starting RL Agent service...")
    
    cmd = [sys.executable, "-m", "app.services.rl_agent"]
    process = subprocess.Popen(cmd)
    processes.append(process)
    return process


def start_file_monitor():
    """파일 모니터링 서비스 시작"""
    logger.info("Starting File Monitor service...")
    
    cmd = [sys.executable, "-m", "app.services.file_monitor"]
    process = subprocess.Popen(cmd)
    processes.append(process)
    return process


def start_redis():
    """Redis 서버 시작 (Docker 사용)"""
    logger.info("Starting Redis server...")
    
    try:
        # Docker로 Redis 시작
        cmd = ["docker", "run", "--rm", "-d", "-p", "6379:6379", "redis:7-alpine"]
        process = subprocess.Popen(cmd)
        processes.append(process)
        return process
    except Exception as e:
        logger.warning(f"Failed to start Redis with Docker: {e}")
        logger.info("Please start Redis manually or use Docker Compose")
        return None


def start_postgres():
    """PostgreSQL 서버 시작 (Docker 사용)"""
    logger.info("Starting PostgreSQL server...")
    
    try:
        # Docker로 PostgreSQL 시작
        cmd = [
            "docker", "run", "--rm", "-d",
            "-p", "5432:5432",
            "-e", "POSTGRES_DB=medical_cybersecurity",
            "-e", "POSTGRES_USER=postgres",
            "-e", "POSTGRES_PASSWORD=postgres",
            "postgres:15-alpine"
        ]
        process = subprocess.Popen(cmd)
        processes.append(process)
        return process
    except Exception as e:
        logger.warning(f"Failed to start PostgreSQL with Docker: {e}")
        logger.info("Please start PostgreSQL manually or use Docker Compose")
        return None


def check_dependencies():
    """의존성 확인"""
    logger.info("Checking dependencies...")
    
    # Python 패키지 확인
    required_packages = [
        "fastapi", "uvicorn", "sqlalchemy", "alembic",
        "torch", "stable_baselines3", "watchdog"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Please run: pip install -r requirements.txt")
        return False
    
    # Rust 확인
    try:
        subprocess.run(["cargo", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Rust is not installed. Please install Rust first.")
        return False
    
    # Rust 암호화 엔진 확인
    rust_lib_path = Path("rust_crypto/target/release")
    if not rust_lib_path.exists():
        logger.error("Rust crypto engine not built. Please run: cargo build --release")
        return False
    
    return True


def wait_for_service(host, port, service_name, timeout=30):
    """서비스 시작 대기"""
    import socket
    
    logger.info(f"Waiting for {service_name} to start...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                logger.info(f"{service_name} is ready!")
                return True
        except Exception:
            pass
        
        time.sleep(1)
    
    logger.error(f"{service_name} failed to start within {timeout} seconds")
    return False


def main():
    """메인 함수"""
    logger.info("🏥 Medical Cybersecurity System - Starting Services")
    logger.info("=" * 60)
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 의존성 확인
    if not check_dependencies():
        logger.error("Dependency check failed. Exiting.")
        sys.exit(1)
    
    # 환경 변수 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        # 데이터베이스 서비스 시작
        postgres_process = start_postgres()
        if postgres_process:
            wait_for_service("localhost", 5432, "PostgreSQL", 60)
        
        # Redis 서비스 시작
        redis_process = start_redis()
        if redis_process:
            wait_for_service("localhost", 6379, "Redis", 30)
        
        # 데이터베이스 마이그레이션
        logger.info("Running database migrations...")
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        
        # FastAPI 서버 시작
        fastapi_process = start_fastapi_server()
        wait_for_service("localhost", 8000, "FastAPI Server", 30)
        
        # RL 에이전트 시작
        rl_process = start_rl_agent()
        
        # 파일 모니터링 시작
        monitor_process = start_file_monitor()
        
        logger.info("✅ All services started successfully!")
        logger.info("")
        logger.info("🌐 API Server: http://localhost:8000")
        logger.info("📊 Monitoring Dashboard: http://localhost:8000/api/v1/monitoring/dashboard")
        logger.info("📚 API Documentation: http://localhost:8000/docs")
        logger.info("")
        logger.info("Press Ctrl+C to stop all services")
        
        # 서비스 상태 모니터링
        while True:
            time.sleep(5)
            
            # 프로세스 상태 확인
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    logger.error(f"Service {i} has stopped unexpectedly")
                    return
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Error starting services: {e}")
    finally:
        # 모든 서비스 종료
        signal_handler(None, None)


if __name__ == "__main__":
    main()