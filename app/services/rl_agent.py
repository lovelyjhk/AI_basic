"""
Reinforcement Learning Agent for Cybersecurity Threat Detection
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Tuple, Optional, Any
import logging
from pathlib import Path
import json
import hashlib
from datetime import datetime

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback
import gymnasium as gym

logger = logging.getLogger(__name__)


class CybersecurityEnv(gym.Env):
    """사이버보안 위협 탐지를 위한 강화학습 환경"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()
        
        self.config = config or {}
        self.max_steps = self.config.get("max_steps", 1000)
        self.current_step = 0
        
        # 네트워크 패킷 특성 (관찰 공간)
        # [패킷 크기, 프로토콜, 포트, 플래그, 페이로드 해시, 시간 간격]
        self.observation_space = gym.spaces.Box(
            low=0, high=1, shape=(6,), dtype=np.float32
        )
        
        # 액션 공간: [무시, 경고, 차단, 격리, 분석]
        self.action_space = gym.spaces.Discrete(5)
        
        # 액션 매핑
        self.action_mapping = {
            0: "ignore",
            1: "warn", 
            2: "block",
            3: "quarantine",
            4: "analyze"
        }
        
        # 상태 초기화
        self.reset()
    
    def reset(self, seed=None, options=None):
        """환경 초기화"""
        super().reset(seed=seed)
        self.current_step = 0
        self.current_observation = self._generate_observation()
        return self.current_observation, {}
    
    def step(self, action):
        """한 스텝 실행"""
        self.current_step += 1
        
        # 액션 실행
        reward = self._execute_action(action)
        
        # 다음 관찰 생성
        self.current_observation = self._generate_observation()
        
        # 종료 조건 확인
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        info = {
            "action": self.action_mapping[action],
            "step": self.current_step
        }
        
        return self.current_observation, reward, terminated, truncated, info
    
    def _generate_observation(self) -> np.ndarray:
        """관찰 생성 (네트워크 패킷 특성 시뮬레이션)"""
        # 실제로는 네트워크 패킷에서 추출한 특성 사용
        observation = np.random.random(6).astype(np.float32)
        return observation
    
    def _execute_action(self, action: int) -> float:
        """액션 실행 및 리워드 계산"""
        action_name = self.action_mapping[action]
        
        # 시뮬레이션된 위협 레벨 (0-1)
        threat_level = np.random.random()
        
        # 리워드 계산
        if action_name == "ignore":
            if threat_level > 0.7:  # 실제 위협인데 무시
                return -1.0  # False Negative 페널티
            else:
                return 0.1   # 정상 트래픽 무시 보상
                
        elif action_name == "warn":
            if threat_level > 0.5:
                return 0.5   # 위협 경고 보상
            else:
                return -0.2  # False Positive 페널티
                
        elif action_name == "block":
            if threat_level > 0.8:
                return 1.0   # 위협 차단 보상
            else:
                return -0.5  # 과도한 차단 페널티
                
        elif action_name == "quarantine":
            if threat_level > 0.9:
                return 0.8   # 위협 격리 보상
            else:
                return -0.3  # 불필요한 격리 페널티
                
        elif action_name == "analyze":
            if threat_level > 0.6:
                return 0.3   # 분석 시작 보상
            else:
                return -0.1  # 불필요한 분석 페널티
        
        return 0.0


class ThreatAnalyzer:
    """위협 분석기 (RL 에이전트 기반)"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or "/app/models/rl_agent.pkl"
        self.model = None
        self.env = None
        self.is_trained = False
        
        # 모델 로드 시도
        self._load_model()
    
    def _load_model(self):
        """훈련된 모델 로드"""
        try:
            if Path(self.model_path).exists():
                self.model = PPO.load(self.model_path)
                self.is_trained = True
                logger.info("Pre-trained RL model loaded successfully")
            else:
                logger.warning("No pre-trained model found, using random policy")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    
    def train(self, total_timesteps: int = 100000, save_path: str = None):
        """RL 에이전트 훈련"""
        logger.info("Starting RL agent training...")
        
        # 환경 생성
        self.env = CybersecurityEnv()
        vec_env = make_vec_env(lambda: CybersecurityEnv(), n_envs=4)
        
        # PPO 모델 생성
        self.model = PPO(
            "MlpPolicy",
            vec_env,
            verbose=1,
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01
        )
        
        # 훈련 실행
        self.model.learn(total_timesteps=total_timesteps)
        
        # 모델 저장
        save_path = save_path or self.model_path
        self.model.save(save_path)
        self.is_trained = True
        
        logger.info(f"Training completed. Model saved to {save_path}")
    
    def analyze_file(self, file_path: str, file_hash: str = None) -> Dict[str, Any]:
        """파일 위협 분석"""
        logger.info(f"Analyzing file: {file_path}")
        
        # 파일 특성 추출
        file_features = self._extract_file_features(file_path, file_hash)
        
        if not self.is_trained:
            # 훈련되지 않은 경우 휴리스틱 분석
            return self._heuristic_analysis(file_features)
        
        # RL 에이전트를 통한 분석
        return self._rl_analysis(file_features)
    
    def _extract_file_features(self, file_path: str, file_hash: str = None) -> Dict[str, Any]:
        """파일에서 특성 추출"""
        features = {}
        
        try:
            path = Path(file_path)
            
            # 기본 파일 정보
            features["file_size"] = path.stat().st_size
            features["file_extension"] = path.suffix.lower()
            features["file_name_length"] = len(path.name)
            
            # 파일 해시 계산
            if not file_hash:
                file_hash = self._calculate_file_hash(file_path)
            features["file_hash"] = file_hash
            
            # 파일 내용 분석
            features.update(self._analyze_file_content(file_path))
            
        except Exception as e:
            logger.error(f"Failed to extract features from {file_path}: {e}")
            features["error"] = str(e)
        
        return features
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def _analyze_file_content(self, file_path: str) -> Dict[str, Any]:
        """파일 내용 분석"""
        content_features = {}
        
        try:
            with open(file_path, "rb") as f:
                content = f.read(1024)  # 첫 1KB만 읽기
            
            # 바이트 분포 분석
            byte_counts = [content.count(bytes([i])) for i in range(256)]
            content_features["entropy"] = self._calculate_entropy(byte_counts)
            content_features["null_bytes"] = content.count(b'\x00')
            content_features["printable_ratio"] = sum(1 for b in content if 32 <= b <= 126) / len(content)
            
            # 의심스러운 패턴 검사
            content_features["suspicious_patterns"] = self._detect_suspicious_patterns(content)
            
        except Exception as e:
            logger.error(f"Failed to analyze content of {file_path}: {e}")
            content_features["error"] = str(e)
        
        return content_features
    
    def _calculate_entropy(self, byte_counts: List[int]) -> float:
        """엔트로피 계산"""
        total = sum(byte_counts)
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in byte_counts:
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)
        
        return entropy
    
    def _detect_suspicious_patterns(self, content: bytes) -> List[str]:
        """의심스러운 패턴 탐지"""
        patterns = []
        
        # 알려진 악성코드 시그니처
        malicious_signatures = [
            b"MZ",  # PE 파일
            b"<script",  # JavaScript
            b"eval(",  # JavaScript eval
            b"base64",  # Base64 인코딩
            b"powershell",  # PowerShell
            b"cmd.exe",  # Command execution
        ]
        
        content_lower = content.lower()
        for signature in malicious_signatures:
            if signature in content_lower:
                patterns.append(signature.decode())
        
        return patterns
    
    def _heuristic_analysis(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """휴리스틱 기반 분석"""
        threat_score = 0.0
        indicators = []
        
        # 파일 크기 기반 분석
        file_size = features.get("file_size", 0)
        if file_size > 100 * 1024 * 1024:  # 100MB 이상
            threat_score += 0.2
            indicators.append("large_file_size")
        
        # 엔트로피 기반 분석
        entropy = features.get("entropy", 0)
        if entropy > 7.5:  # 높은 엔트로피 (암호화/압축)
            threat_score += 0.3
            indicators.append("high_entropy")
        
        # 의심스러운 패턴
        suspicious_patterns = features.get("suspicious_patterns", [])
        if suspicious_patterns:
            threat_score += 0.4
            indicators.extend(suspicious_patterns)
        
        # 파일 확장자 기반
        extension = features.get("file_extension", "").lower()
        suspicious_extensions = [".exe", ".bat", ".cmd", ".scr", ".pif"]
        if extension in suspicious_extensions:
            threat_score += 0.2
            indicators.append(f"suspicious_extension_{extension}")
        
        # 위협 레벨 결정
        if threat_score > 0.7:
            threat_level = "high"
        elif threat_score > 0.4:
            threat_level = "medium"
        else:
            threat_level = "low"
        
        return {
            "threat_detected": threat_score > 0.3,
            "threat_score": threat_score,
            "threat_level": threat_level,
            "confidence": min(threat_score, 1.0),
            "indicators": indicators,
            "analysis_method": "heuristic"
        }
    
    def _rl_analysis(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """RL 에이전트 기반 분석"""
        # 특성을 관찰 벡터로 변환
        observation = self._features_to_observation(features)
        
        # 에이전트 예측
        action, _states = self.model.predict(observation, deterministic=True)
        
        # 액션을 위협 분석 결과로 변환
        return self._action_to_analysis(action, features)
    
    def _features_to_observation(self, features: Dict[str, Any]) -> np.ndarray:
        """특성을 관찰 벡터로 변환"""
        # 정규화된 특성 벡터 생성
        observation = np.zeros(6, dtype=np.float32)
        
        # 파일 크기 정규화 (0-1)
        file_size = features.get("file_size", 0)
        observation[0] = min(file_size / (100 * 1024 * 1024), 1.0)  # 100MB 기준
        
        # 엔트로피 정규화 (0-1)
        entropy = features.get("entropy", 0)
        observation[1] = min(entropy / 8.0, 1.0)  # 최대 엔트로피 8
        
        # 의심스러운 패턴 수 (0-1)
        suspicious_count = len(features.get("suspicious_patterns", []))
        observation[2] = min(suspicious_count / 5.0, 1.0)
        
        # 파일 확장자 위험도 (0-1)
        extension = features.get("file_extension", "").lower()
        risky_extensions = [".exe", ".bat", ".cmd", ".scr", ".pif", ".vbs", ".js"]
        observation[3] = 1.0 if extension in risky_extensions else 0.0
        
        # Null 바이트 비율 (0-1)
        null_bytes = features.get("null_bytes", 0)
        content_length = min(features.get("file_size", 1024), 1024)
        observation[4] = min(null_bytes / content_length, 1.0) if content_length > 0 else 0.0
        
        # 인쇄 가능 문자 비율 (0-1)
        observation[5] = features.get("printable_ratio", 0.0)
        
        return observation
    
    def _action_to_analysis(self, action: int, features: Dict[str, Any]) -> Dict[str, Any]:
        """액션을 분석 결과로 변환"""
        action_mapping = {
            0: {"threat_detected": False, "confidence": 0.1, "action": "ignore"},
            1: {"threat_detected": True, "confidence": 0.3, "action": "warn"},
            2: {"threat_detected": True, "confidence": 0.7, "action": "block"},
            3: {"threat_detected": True, "confidence": 0.8, "action": "quarantine"},
            4: {"threat_detected": True, "confidence": 0.5, "action": "analyze"}
        }
        
        result = action_mapping.get(action, action_mapping[0])
        
        # 위협 레벨 결정
        if result["threat_detected"]:
            if result["confidence"] > 0.7:
                threat_level = "high"
            elif result["confidence"] > 0.4:
                threat_level = "medium"
            else:
                threat_level = "low"
        else:
            threat_level = "none"
        
        return {
            "threat_detected": result["threat_detected"],
            "confidence": result["confidence"],
            "threat_level": threat_level,
            "recommended_action": result["action"],
            "analysis_method": "rl_agent",
            "indicators": features.get("suspicious_patterns", [])
        }


# 전역 위협 분석기 인스턴스
threat_analyzer = ThreatAnalyzer()


def train_rl_agent():
    """RL 에이전트 훈련 함수"""
    analyzer = ThreatAnalyzer()
    analyzer.train(total_timesteps=100000)
    logger.info("RL agent training completed")


if __name__ == "__main__":
    # 훈련 실행
    train_rl_agent()