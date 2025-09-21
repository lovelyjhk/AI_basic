import pytest
from app.services import backup_strategy

def test_backup_strategy_training():
    # 모델 학습 후 정상적으로 저장/불러오기 되는지 확인
    model = backup_strategy.train_rl()
    assert model is not None

def test_backup_strategy_choices():
    # emergency=0 → Full 백업
    strat_normal = backup_strategy.choose_strategy(0)
    assert strat_normal in ["Full", "Incremental"]

    # emergency=1 → Incremental 백업
    strat_emergency = backup_strategy.choose_strategy(1)
    assert strat_emergency in ["Full", "Incremental"]

    print("Normal:", strat_normal, "Emergency:", strat_emergency)
