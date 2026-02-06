# FILE: src/core/env.py
import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces


class TradingEnv(gym.Env):
    def __init__(self, df: pd.DataFrame, initial_balance=10000, mistakes_data=None):
        super(TradingEnv, self).__init__()

        # Store original df with datetime index for timestamp comparison
        self.original_df = df
        # Create a copy with reset index for the main operations
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.mistakes_data = mistakes_data or {}

        # Action: 0=Hold, 1=Buy, 2=Sell
        self.action_space = spaces.Discrete(3)

        # Observation: Fitur-fitur dari DataFrame (kecuali timestamp/metadata)
        # Asumsi data masuk sudah di-scale oleh FeatureEngineer sebelumnya
        exclude_cols = ["timestamp", "date", "symbol", "target"]
        self.feature_cols = [c for c in df.columns if c not in exclude_cols]

        # Define observation space bounds
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(len(self.feature_cols),), dtype=np.float32
        )

        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0  # 0: No pos, >0: Shares held
        self.avg_price = 0
        self.net_worth = self.initial_balance
        self.history = []

        return self._next_observation(), {}

    def _next_observation(self):
        # Ambil baris data saat ini
        # Fix Pylance type error by using iloc for row selection first
        row_data = self.df.iloc[self.current_step]
        obs = row_data[self.feature_cols].values
        return obs.astype(np.float32)

    def step(self, action):
        # Get current price with explicit type conversion to avoid Pylance errors
        close_value = self.df.loc[self.current_step, "Close"]
        current_price = (
            float(close_value) if isinstance(close_value, (int, float)) else 0.0
        )

        # Logika Trading Sederhana
        reward = 0
        done = False

        # Check if current timestamp matches any historical mistakes
        # Get timestamp from original df's DatetimeIndex and convert to string format
        current_datetime = self.original_df.index[self.current_step]
        current_timestamp = current_datetime.strftime("%Y-%m-%d %H:00:00")

        if current_timestamp in self.mistakes_data:
            mistake_action = self.mistakes_data[current_timestamp]
            if action == mistake_action:
                # Penalize heavily for repeating historical mistakes
                reward -= 1000  # Large negative reward

        if action == 1:  # BUY
            if self.balance >= current_price:
                # Beli semampunya (simplified logic, real logic in agent.py)
                shares_to_buy = self.balance // current_price
                cost = shares_to_buy * current_price
                self.balance -= cost

                # Update average price
                total_shares = self.position + shares_to_buy
                total_cost = (self.position * self.avg_price) + cost
                self.avg_price = total_cost / total_shares if total_shares > 0 else 0
                self.position = total_shares

        elif action == 2:  # SELL
            if self.position > 0:
                # Jual semua
                revenue = self.position * current_price
                profit = revenue - (self.position * self.avg_price)
                self.balance += revenue
                self.position = 0
                self.avg_price = 0

                # Reward based on profit
                reward = profit

        # Update Net Worth
        current_val = self.balance + (self.position * current_price)
        self.net_worth = current_val

        # Step forward
        self.current_step += 1

        if self.current_step >= len(self.df) - 1:
            done = True

        return self._next_observation(), reward, done, False, {}

    def render(self, mode="human"):
        print(f"Step: {self.current_step}, Net Worth: {self.net_worth:.2f}")
