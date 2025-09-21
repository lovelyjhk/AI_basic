import pytest
from app.services import detector

def test_detector_accuracy():
    acc, important = detector.train_and_detect()
    # 정확도는 0~1 사이 값
    assert 0 <= acc <= 1
    # 중요 컬럼은 최소 1개 이상
    assert len(important) > 0
    print("탐지 정확도:", acc, "중요 컬럼:", important)
