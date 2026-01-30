import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces

from src.core.logger import logger


class TradingEnvironment(gym.Env):
    """
    Lingkungan Simulasi Pasar Saham (Gymnasium Compatible).
    AI akan melihat data teknikal & bandarmology, lalu memutuskan aksi (Buy/Sell/Hold).
    """

    metadata = {"render.modes": ["human"]}

    def __init__(self, df: pd.DataFrame, initial_balance=100_000_000):
        super(TradingEnvironment, self).__init__()

        self.df = df
        self.initial_balance = initial_balance
        self.current_step = 0

        # --- 1. ACTION SPACE (Apa yang bisa dilakukan AI?) ---
        # 0 = Hold
        # 1 = Buy (10% Modal)
        # 2 = Sell (Jual Semua)
        self.action_space = spaces.Discrete(3)

        # --- 2. OBSERVATION SPACE (Apa yang dilihat AI?) ---
        # Kita asumsikan ada 5 fitur utama:
        # [Close Price (Norm), RSI, MACD, Bandar Flow, Volatility]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32
        )

    def reset(self, seed=None, options=None):
        """Reset state untuk episode training baru"""
        super().reset(seed=seed)
        self.balance = self.initial_balance
        self.shares_held = 0
        self.net_worth = self.initial_balance
        self.current_step = 0
        self.history = []

        return self._next_observation(), {}

    def _next_observation(self):
        """Ambil data pasar pada detik ini"""
        frame = self.df.iloc[self.current_step]

        # Pastikan urutan fitur konsisten!
        obs = np.array(
            [
                frame["close_scaled"],  # Harga dinormalisasi
                frame["rsi"] / 100,  # RSI dinormalisasi 0-1
                frame["macd"],
                frame["bandar_accum_score"],  # Skor Bandarmology
                frame["volatility"],
            ],
            dtype=np.float32,
        )

        return obs

    def step(self, action):
        """AI melakukan aksi -> Environment memberikan Reward/Punishment"""
        current_price = self.df.iloc[self.current_step]["close"]

        # -- EKSEKUSI AKSI --
        if action == 1:  # BUY
            # Hanya beli jika punya cash dan belum pegang barang (Simple Logic)
            if self.balance > current_price and self.shares_held == 0:
                shares_to_buy = int(self.balance // current_price)
                cost = shares_to_buy * current_price
                self.balance -= cost
                self.shares_held += shares_to_buy

        elif action == 2:  # SELL
            if self.shares_held > 0:
                revenue = self.shares_held * current_price
                self.balance += revenue
                self.shares_held = 0

        # -- HITUNG REWARD (Bagian Paling Penting) --
        # Kita pakai strategi: Reward = Change in Net Worth
        prev_net_worth = self.net_worth
        self.net_worth = self.balance + (self.shares_held * current_price)

        reward = self.net_worth - prev_net_worth

        # Tambahan: Punishment jika Drawdown terlalu dalam (Risk Management)
        if reward < 0:
            reward *= 1.5  # Sakiti AI lebih keras jika rugi (agar dia hati-hati)

        # -- NEXT STEP --
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1

        truncated = False
        info = {"net_worth": self.net_worth}

        return self._next_observation(), reward, done, truncated, info

    def render(self, mode="human"):
        logger.info(f"Step: {self.current_step}, Net Worth: {self.net_worth}")
