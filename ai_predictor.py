"""
AI 예측 모듈 (랜섬웨어 탐지)
석사 논문용 MVP - RandomForest 기반 사전 학습 모델
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RansomwareDetector:
    """랜섬웨어 탐지 AI 모델"""
    
    def __init__(self, model_path: str = "models/ransomware_detector.pkl"):
        self.model_path = model_path
        self.model = None
        self.feature_names = [
            'files_modified_per_sec',
            'bytes_written_per_sec',
            'file_entropy',
            'process_cpu_usage',
            'suspicious_extensions',
            'rapid_file_changes',
            'unauthorized_access',
            'network_anomaly',
        ]
    
    def create_synthetic_dataset(self, n_samples: int = 10000) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        합성 학습 데이터셋 생성 (의료 환경 특화)
        
        정상 행위:
        - files_modified_per_sec: 0-10
        - bytes_written_per_sec: 0-1MB
        - file_entropy: 낮음 (의료 데이터는 구조화됨)
        
        랜섬웨어 행위:
        - files_modified_per_sec: 50-500
        - bytes_written_per_sec: 10MB-100MB
        - file_entropy: 높음 (암호화된 데이터)
        """
        np.random.seed(42)
        
        normal_samples = n_samples // 2
        attack_samples = n_samples - normal_samples
        
        # 정상 행위 데이터
        normal_data = {
            'files_modified_per_sec': np.random.uniform(0, 10, normal_samples),
            'bytes_written_per_sec': np.random.uniform(0, 1_000_000, normal_samples),
            'file_entropy': np.random.uniform(3.0, 5.0, normal_samples),
            'process_cpu_usage': np.random.uniform(5, 30, normal_samples),
            'suspicious_extensions': np.random.binomial(1, 0.01, normal_samples),
            'rapid_file_changes': np.random.binomial(1, 0.05, normal_samples),
            'unauthorized_access': np.random.binomial(1, 0.02, normal_samples),
            'network_anomaly': np.random.binomial(1, 0.03, normal_samples),
        }
        
        # 랜섬웨어 공격 데이터
        attack_data = {
            'files_modified_per_sec': np.random.uniform(50, 500, attack_samples),
            'bytes_written_per_sec': np.random.uniform(10_000_000, 100_000_000, attack_samples),
            'file_entropy': np.random.uniform(7.5, 8.0, attack_samples),
            'process_cpu_usage': np.random.uniform(60, 100, attack_samples),
            'suspicious_extensions': np.random.binomial(1, 0.8, attack_samples),
            'rapid_file_changes': np.random.binomial(1, 0.9, attack_samples),
            'unauthorized_access': np.random.binomial(1, 0.7, attack_samples),
            'network_anomaly': np.random.binomial(1, 0.6, attack_samples),
        }
        
        # 데이터프레임 생성
        df_normal = pd.DataFrame(normal_data)
        df_attack = pd.DataFrame(attack_data)
        
        df = pd.concat([df_normal, df_attack], ignore_index=True)
        labels = np.concatenate([np.zeros(normal_samples), np.ones(attack_samples)])
        
        # 셔플
        indices = np.random.permutation(len(df))
        df = df.iloc[indices].reset_index(drop=True)
        labels = labels[indices]
        
        logger.info(f"생성된 데이터셋: {len(df)} 샘플 (정상: {normal_samples}, 공격: {attack_samples})")
        
        return df, labels
    
    def train(self, X: pd.DataFrame, y: np.ndarray) -> Dict[str, float]:
        """모델 학습"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"학습 데이터: {len(X_train)} 샘플")
        logger.info(f"테스트 데이터: {len(X_test)} 샘플")
        
        # RandomForest 모델 학습
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # 성능 평가
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
        }
        
        logger.info(f"모델 성능:")
        for metric, value in metrics.items():
            logger.info(f"  {metric}: {value:.4f}")
        
        # Feature Importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info("\nFeature Importance:")
        logger.info(feature_importance.to_string())
        
        return metrics
    
    def save_model(self):
        """모델 저장"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"모델 저장: {self.model_path}")
    
    def load_model(self):
        """모델 로드"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info(f"모델 로드: {self.model_path}")
        else:
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {self.model_path}")
    
    def predict(self, features: Dict[str, float]) -> Tuple[bool, float]:
        """
        랜섬웨어 탐지 예측
        
        Returns:
            (is_attack, threat_score) - is_attack: 공격 여부, threat_score: 위협 점수 (0~1)
        """
        if self.model is None:
            raise ValueError("모델이 로드되지 않았습니다. load_model() 또는 train()을 먼저 실행하세요.")
        
        # Feature 벡터 생성
        X = pd.DataFrame([features])[self.feature_names]
        
        # 예측
        prediction = self.model.predict(X)[0]
        threat_score = self.model.predict_proba(X)[0][1]
        
        return bool(prediction), float(threat_score)
    
    def predict_batch(self, features_list: List[Dict[str, float]]) -> List[Tuple[bool, float]]:
        """배치 예측"""
        if self.model is None:
            raise ValueError("모델이 로드되지 않았습니다.")
        
        X = pd.DataFrame(features_list)[self.feature_names]
        predictions = self.model.predict(X)
        threat_scores = self.model.predict_proba(X)[:, 1]
        
        return list(zip(predictions.astype(bool), threat_scores.astype(float)))


def train_and_save_model():
    """모델 학습 및 저장 (초기 실행용)"""
    detector = RansomwareDetector()
    
    # 데이터셋 생성
    X, y = detector.create_synthetic_dataset(n_samples=50000)
    
    # 학습
    metrics = detector.train(X, y)
    
    # 저장
    detector.save_model()
    
    return detector, metrics


if __name__ == "__main__":
    # 모델 학습 및 저장
    detector, metrics = train_and_save_model()
    
    # 테스트 예측
    normal_features = {
        'files_modified_per_sec': 5.0,
        'bytes_written_per_sec': 500_000.0,
        'file_entropy': 4.2,
        'process_cpu_usage': 15.0,
        'suspicious_extensions': 0,
        'rapid_file_changes': 0,
        'unauthorized_access': 0,
        'network_anomaly': 0,
    }
    
    attack_features = {
        'files_modified_per_sec': 250.0,
        'bytes_written_per_sec': 50_000_000.0,
        'file_entropy': 7.8,
        'process_cpu_usage': 85.0,
        'suspicious_extensions': 1,
        'rapid_file_changes': 1,
        'unauthorized_access': 1,
        'network_anomaly': 1,
    }
    
    is_attack, threat_score = detector.predict(normal_features)
    print(f"\n정상 행위 예측: 공격={is_attack}, 위협점수={threat_score:.4f}")
    
    is_attack, threat_score = detector.predict(attack_features)
    print(f"공격 행위 예측: 공격={is_attack}, 위협점수={threat_score:.4f}")
