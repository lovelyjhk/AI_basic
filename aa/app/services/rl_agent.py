import numpy as np
import gym
from gym import spaces
import random
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

MODEL_PATH = "backup_rl_model"

class BackupEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(0,1,shape=(1,),dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self.reset()

    def reset(self):
        self.emergency = random.choice([0,1])
        return np.array([self.emergency], dtype=np.float32)

    def step(self, action):
        reward = 0
        if self.emergency==1:
            reward = 1 if action==1 else -1
        else:
            reward = 1 if action==0 else 0
        done = True
        return np.array([self.emergency], dtype=np.float32), reward, done, {}

def train_rl():
    vec_env = make_vec_env(lambda: BackupEnv(), n_envs=4)
    model = PPO("MlpPolicy", vec_env, verbose=0)
    model.learn(total_timesteps=5000)
    model.save(MODEL_PATH)
    return model

def choose_strategy(emergency_flag: int):
    try:
        model = PPO.load(MODEL_PATH)
    except:
        model = train_rl()
    obs = np.array([emergency_flag], dtype=np.float32)
    action,_ = model.predict(obs, deterministic=True)
    return "Incremental" if action[0]==1 else "Full"
