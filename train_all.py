import os

from stable_baselines3 import PPO

from src.core.config_assets import ASSETS
from src.core.data_loader import fetch_data
from src.core.env import AdvancedForexEnv


def run():
    for cat, items in ASSETS.items():
        for sym in items:
            print(f"Training {sym}...")
            df = fetch_data(sym, period="2y")
            if df.empty:
                continue

            env = AdvancedForexEnv(df)
            model = PPO("MlpPolicy", env, verbose=0)
            model.learn(total_timesteps=10000)

            path = f"models/{cat.lower()}/{sym.replace('=','').replace('^','')}.zip"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            model.save(path)


if __name__ == "__main__":
    run()
