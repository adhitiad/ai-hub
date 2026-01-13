import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces
from sklearn.preprocessing import StandardScaler

from src.core.feature_engineering import FEATURE_COLUMNS, get_model_input
from src.core.logger import logging


class AdvancedForexEnv(gym.Env):
    """
    Custom Environment Trading dengan Normalisasi Data
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        df,
        initial_balance=1000,
        spread=0.0002,
        commission=0.0,
        mistakes_data=None,
    ):
        super(AdvancedForexEnv, self).__init__()

        # Copy dataframe agar tidak merusak data asli
        self.raw_df = df.copy()
        self.spread = spread
        self.commission = commission
        self.mistakes_data = mistakes_data if mistakes_data else {}

        # --- FEATURE ENGINEERING CENTRALIZED ---
        # Ambil hanya kolom fitur ML yang baku
        self.features_df = get_model_input(df)

        # --- NORMALISASI DATA (CRITICAL FIX) ---
        # AI akan gagal paham jika inputnya campuran harga (1.000.000) dan RSI (50)
        # Kita scale semua kolom numerik menjadi range rata-rata 0, deviasi 1
        self.scaler = StandardScaler()
        self.scaled_features = self.scaler.fit_transform(self.features_df)

        # Setup Gym
        self.max_steps = len(df) - 1
        self.balance = initial_balance
        self.net_worth = initial_balance
        self.position = 0
        self.entry_price = 0

        self.action_space = spaces.Discrete(3)

        # Hapus kolom non-numerik jika ada (jaga-jaga)
        numeric_df = self.raw_df.select_dtypes(include=[np.number])

        # Fit & Transform seluruh data (Note: Utk production ketat, gunakan window scaling)
        # Tapi untuk fix cepat & stabil, scaling global di awal sudah jauh lebih baik dari raw.
        self.scaled_data = self.scaler.fit_transform(numeric_df)

        # Simpan nama kolom untuk referensi debug
        self.feature_columns = numeric_df.columns

        # Shape Observation: Jumlah Fitur Baku + 1 (Posisi)
        # Dijamin konsisten karena pakai FEATURE_COLUMNS dari feature_engineering.py
        self.shape = (len(FEATURE_COLUMNS) + 1,)

        # --- Observation Space ---
        # Shape: Jumlah Fitur di DF + 1 (Status Posisi)
        self.shape = (self.scaled_data.shape[1] + 1,)

        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=self.shape, dtype=np.float32
        )

        self.reset()

    def _next_observation(self):
        # Ambil data TERNORMALISASI (Scaled), bukan data raw
        frame = self.scaled_data[self.current_step]

        # Gabungkan dengan info posisi kita
        obs = np.append(frame, [self.position])

        return obs.astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.balance = 100000
        self.net_worth = 100000
        self.position = 0
        self.entry_price = 0
        self.current_step = 0

        return self._next_observation(), {}

    def step(self, action):
        self.current_step += 1

        # Ambil Harga ASLI (Raw) untuk hitung profit/loss beneran
        current_price = self.raw_df.iloc[self.current_step]["Close"]

        reward = 0
        prev_net_worth = self.net_worth

        # 1. Eksekusi Action
        if action == 1 and self.position == 0:  # OPEN BUY
            self.position = 1
            self.entry_price = current_price + self.spread
            reward -= self.spread  # Cost spread

        elif action == 2 and self.position == 1:  # CLOSE BUY
            self.position = 0
            profit = current_price - self.entry_price - self.commission
            self.balance += profit
            # Reward berdasarkan % gain agar konsisten antar aset
            pct_gain = (profit / self.entry_price) * 100
            reward += pct_gain * 10

        # 2. Update Net Worth
        if self.position == 1:
            unrealized_pnl = current_price - self.entry_price
            self.net_worth = self.balance + unrealized_pnl
        else:
            self.net_worth = self.balance

        # 3. Reward Shaping
        # Reward kecil setiap step jika net worth naik
        reward += (self.net_worth - prev_net_worth) * 0.1

        # 4. Terminated?
        terminated = self.current_step >= self.max_steps
        if self.net_worth <= (self.balance * 0.5):  # Stop jika rugi 50%
            terminated = True
            reward -= 100

        truncated = False

        # 5. Reflection Learning (Mistakes Database)
        current_time_idx = self.raw_df.index[self.current_step]
        current_time_str = str(current_time_idx)

        if current_time_str in self.mistakes_data:
            past_bad_action = self.mistakes_data[current_time_str]
            if action == past_bad_action:
                reward -= 50  # Penalti besar karena mengulangi kesalahan

        info = {
            "balance": self.balance,
            "net_worth": self.net_worth,
            "step": self.current_step,
        }

        return self._next_observation(), reward, terminated, truncated, info

    def render(self, mode="human"):
        logging.info(f"Step: {self.current_step}, Net Worth: {self.net_worth}")
