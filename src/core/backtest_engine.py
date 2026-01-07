import os

import numpy as np
import pandas as pd
from stable_baselines3 import PPO

from src.core.config_assets import get_asset_info
from src.core.data_loader import fetch_data

MODELS_DIR = "models"


def run_backtest_simulation(symbol, period="1y", initial_balance=100000000):
    """
    Menjalankan simulasi AI pada data masa lalu.
    """
    # 1. Ambil Data Historis
    df = fetch_data(symbol, period=period, interval="1h")
    if df.empty:
        return {"error": "Data historis tidak ditemukan"}

    # 2. Load Model AI yang sesuai simbol
    info = get_asset_info(symbol)
    if not info:
        return {"error": "Aset tidak terdaftar"}

    safe_symbol = symbol.replace("=", "").replace("^", "")
    model_path = f"{MODELS_DIR}/{info['category'].lower()}/{safe_symbol}.zip"

    if not os.path.exists(model_path):
        return {"error": f"Model AI untuk {symbol} belum dilatih. Hubungi Owner."}

    model = PPO.load(model_path)

    # 3. Simulasi Loop (Inference)
    balance = initial_balance
    position = 0  # 0: No Pos, 1: Buy
    entry_price = 0
    trades = []
    equity_curve = []

    # Biaya transaksi simulasi
    spread = info.get("pip_scale", 1) * 2  # Asumsi spread 2 pips/tick
    lot_size = 1  # Simplifikasi 1 Lot fix untuk backtest

    # Loop data (Mulai dari data ke-50 agar indikator stabil)
    for i in range(50, len(df)):
        # Construct Observation (Sama seperti di src/core/env.py)
        row = df.iloc[i]
        obs = np.append(row.values, [position]).astype(np.float32)

        # Predict Action
        action, _ = model.predict(obs, deterministic=True)

        current_price = row["Close"]
        date = df.index[i]

        # --- LOGIKA TRADING ---
        # Action 1: BUY
        if action == 1 and position == 0:
            position = 1
            entry_price = current_price
            trades.append(
                {"date": str(date), "type": "ENTRY BUY", "price": entry_price}
            )

        # Action 2: SELL (Close Buy)
        elif action == 2 and position == 1:
            position = 0
            # Hitung Profit
            diff = current_price - entry_price

            # Logic PnL (Saham vs Forex)
            pnl = 0
            if info["type"] == "stock_indo":
                # 1 Lot = 100 lembar
                pnl = (diff * 100 * lot_size) - (
                    current_price * 0.004 * 100
                )  # Fee 0.4%
            else:
                # Forex logic simple
                pnl = diff * info["lot_multiplier"] * lot_size

            balance += pnl

            trades.append(
                {
                    "date": str(date),
                    "type": "EXIT SELL",
                    "price": current_price,
                    "pnl": round(pnl, 2),
                    "balance_after": round(balance, 2),
                }
            )

        # Catat Equity Harian
        equity_curve.append({"time": str(date), "value": round(balance, 2)})

    # 4. Ringkasan Hasil
    total_trades = len([t for t in trades if t["type"] == "EXIT SELL"])
    win_trades = len([t for t in trades if "pnl" in t and t["pnl"] > 0])
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

    roi = ((balance - initial_balance) / initial_balance) * 100

    return {
        "symbol": symbol,
        "period": period,
        "initial_balance": initial_balance,
        "final_balance": round(balance, 2),
        "roi_percent": f"{round(roi, 2)}%",
        "total_trades": total_trades,
        "win_rate": f"{round(win_rate, 1)}%",
        "trades_log": trades[-20:],  # Tampilkan 20 trade terakhir saja biar ringan
        "equity_curve": equity_curve,  # Untuk Chart
    }
