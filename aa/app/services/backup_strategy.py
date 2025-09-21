import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
import gym
from gym import spaces
import random

MODEL_PATH = "backup_rl_model"

class BackupEnv(gym.Env):
    """
    상태: emergency 여부 (0=일반, 1=응급)
    행동: 0=Full 백업, 1=Incremental 백업
    보상: 상황 맞는 선택시 +1, 틀리면 -1
    """
    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(0, 1, shape=(1,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self.reset()

    def reset(self):
        self.emergency = random.choice([0, 1])
        return np.array([self.emergency], dtype=np.float32)

    def step(self, action):
        reward = 0
        if self.emergency == 1:
            reward = 1 if action == 1 else -1
        else:
            reward = 1 if action == 0 else -1
        done = True
        return np.array([self.emergency], dtype=np.float32), reward, done, {}

def train_rl():
    """RL 학습"""
    vec_env = make_vec_env(lambda: BackupEnv(), n_envs=4)
    model = PPO("MlpPolicy", vec_env, verbose=0)
    model.learn(total_timesteps=5000)
    model.save(MODEL_PATH)
    return model

def choose_strategy(emergency_flag: int):
    """Emergency 플래그에 따라 RL이 결정한 백업 전략 리턴"""
    try:
        model = PPO.load(MODEL_PATH)
    except:
        model = train_rl()
    obs = np.array([emergency_flag], dtype=np.float32)
    action, _ = model.predict(obs, deterministic=True)
    return "Incremental" if action[0] == 1 else "Full"
