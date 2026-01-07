import os
import sys

from stable_baselines3 import PPO

from src.core.config_assets import get_asset_info
from src.core.data_loader import fetch_data
from src.core.env import AdvancedForexEnv
from src.core.torch_config import device

CANDIDATE_DIR = "models/candidates"
PRODUCTION_DIR = "models"


def train_candidate(symbol, total_timesteps=20000):
    """
    Melatih model baru dan menyimpannya di folder 'models/candidates'.
    Tidak langsung menimpa model live.
    """
    try:
        # 1. Fetch Data (Cukup banyak untuk belajar, misal 2 tahun)
        df = fetch_data(symbol, period="2y", interval="1h")
        if df.empty or len(df) < 500:
            return {"success": False, "error": "Data tidak cukup"}

        # 2. Setup Environment
        env = AdvancedForexEnv(df)

        # 3. Setup Model (PPO)
        model = PPO("MlpPolicy", env, verbose=0, device=device)

        # 4. Training Loop
        model.learn(total_timesteps=total_timesteps)

        # 5. Save ke Folder KANDIDAT
        info = get_asset_info(symbol)
        category = info["category"].lower()

        safe_symbol = symbol.replace("=", "").replace("^", "")
        save_path = f"{CANDIDATE_DIR}/{category}/{safe_symbol}.zip"

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        model.save(save_path)

        return {
            "success": True,
            "path": save_path,
            "message": f"Model candidate trained for {symbol}",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def deploy_model(symbol):
    """
    Memindahkan model dari Candidate -> Production (Live).
    Hanya dipanggil jika Backtest sukses.
    """
    import shutil

    info = get_asset_info(symbol)
    category = info["category"].lower()
    safe_symbol = symbol.replace("=", "").replace("^", "")

    src = f"{CANDIDATE_DIR}/{category}/{safe_symbol}.zip"
    dst = f"{PRODUCTION_DIR}/{category}/{safe_symbol}.zip"

    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)
        return True
    return False
