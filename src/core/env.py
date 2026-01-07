import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces

from src.core.logger import logging


class AdvancedForexEnv(gym.Env):
    """
    Custom Environment Trading yang kompatibel dengan Gymnasium & Stable-Baselines3
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

        self.df = df
        self.max_steps = len(df) - 1
        self.spread = spread
        self.commission = commission

        # --- MEMORY INJECTION ---
        # Dictionary berisi { "TIMESTAMP": ACTION_YANG_SALAH }
        self.mistakes_data = mistakes_data if mistakes_data else {}

        # Initialize attributes
        self.net_worth = 1000
        self.position = 0
        self.entry_price = 0

        # --- Action Space ---
        # 0: Hold, 1: Buy, 2: Sell
        self.action_space = spaces.Discrete(3)

        # --- Observation Space ---
        # Kolom Data (OHLCV + Indicators) + 1 Status Posisi
        # Kita pakai Float64 agar presisi, tapi model biasanya minta Float32 (kita cast nanti)
        self.shape = (df.shape[1] + 1,)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=self.shape, dtype=np.float32
        )

        # Inisialisasi state awal
        self.reset()

    def reset(self, seed=None, options=None):
        """
        Reset environment ke kondisi awal.
        Wajib menerima parameter 'seed' dan 'options' di Gymnasium.
        """
        # Set seed untuk reproducibility
        super().reset(seed=seed)

        self.balance = 1000
        self.net_worth = 1000
        self.position = 0  # 0: No Pos, 1: Buy, 2: Sell (Simplifikasi 1 arah dulu)
        self.entry_price = 0
        self.current_step = 0

        # Return Tuple: (Observation, Info Dictionary)
        return self._next_observation(), {}

    def _next_observation(self):
        # Ambil data baris saat ini
        frame = self.df.iloc[self.current_step].values

        # Gabungkan dengan info posisi kita
        obs = np.append(frame, [self.position])

        # Pastikan tipe data float32 agar cocok dengan PyTorch
        return obs.astype(np.float32)

    def step(self, action):
        """
        Melakukan aksi trading.
        Return 5 values: obs, reward, terminated, truncated, info
        """
        self.current_step += 1

        # Harga saat ini
        current_price = self.df.iloc[self.current_step]["Close"]

        reward = 0

        # Logic Trading Sederhana
        prev_net_worth = self.net_worth

        # 1. Eksekusi Action
        if action == 1 and self.position == 0:  # OPEN BUY
            self.position = 1
            self.entry_price = current_price + self.spread
            reward -= self.spread  # Biaya spread langsung minus

        elif action == 2 and self.position == 1:  # CLOSE BUY (SELL)
            self.position = 0
            profit = current_price - self.entry_price - self.commission
            self.balance += profit
            # Reward besar jika profit, hukuman jika rugi
            reward += profit * 10

        # (Tambahkan logika Short Selling jika perlu, disini simplifikasi Long Only dulu)

        # 2. Update Net Worth (Floating Profit)
        if self.position == 1:
            unrealized_pnl = current_price - self.entry_price
            self.net_worth = self.balance + unrealized_pnl
        else:
            self.net_worth = self.balance

        # 3. Reward Shaping (Agar AI cepat belajar)
        # Beri reward jika Net Worth naik
        reward += self.net_worth - prev_net_worth

        # 4. Cek Selesai (Terminated)
        terminated = self.current_step >= self.max_steps

        # Jika bangkrut (Margin Call)
        if self.net_worth <= 0:
            terminated = True
            reward -= 100  # Hukuman berat

        # 5. Truncated (Biasanya False untuk trading, kecuali dibatasi waktu strict)
        truncated = False

        # --- LOGIKA BELAJAR DARI KESALAHAN (REFLECTIVE LEARNING) ---

        # 1. Cek tanggal candle saat ini
        current_time_idx = self.df.index[self.current_step]
        current_time_str = str(current_time_idx)  # Sesuaikan format dengan memory.py

        # 2. Apakah di masa lalu kita pernah rugi di candle ini?
        if current_time_str in self.mistakes_data:
            past_bad_action = self.mistakes_data[current_time_str]

            # 3. Apakah AI mencoba mengulangi aksi bodoh itu?
            if action == past_bad_action:
                # HUKUMAN BERAT!
                # Ini mengajarkan AI: "Dulu kamu BUY di pola ini dan hancur. JANGAN ULANGI!"
                penalty = -500
                reward += penalty

        # 6. Info tambahan
        info = {
            "balance": self.balance,
            "net_worth": self.net_worth,
            "step": self.current_step,
        }

        return self._next_observation(), reward, terminated, truncated, info

    def render(self, mode="human"):
        logging.info(f"Step: {self.current_step}, Net Worth: {self.net_worth}")
