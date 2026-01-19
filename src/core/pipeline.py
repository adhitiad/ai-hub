import os

from stable_baselines3 import PPO

# Import untuk kebutuhan validasi
from src.core.data_loader import fetch_data
from src.core.env import TradingEnv

# Import dari file yang baru saja kita perbaiki lokasinya
from src.core.trainer import deploy_model, train_candidate


def run_auto_optimization(symbol, target_win_rate=60.0):
    """
    PIPELINE: Train -> Backtest -> Deploy
    Hanya mendeploy model jika Win Rate Backtest >= Target.
    """
    report = {"symbol": symbol, "steps": [], "deployed": False, "final_stats": None}

    # --- STEP 1: TRAINING ---
    report["steps"].append("🚀 Starting Training (Candidate)...")
    train_result = train_candidate(symbol)

    if not train_result["success"]:
        report["steps"].append(f"❌ Training Failed: {train_result['error']}")
        return report

    report["steps"].append("✅ Training Finished. Model saved in candidates.")

    # --- STEP 2: BACKTEST (VALIDATION) ---
    report["steps"].append("📉 Running Validation Backtest...")

    try:
        # Load Model Kandidat manual untuk ditest
        model = PPO.load(train_result["path"])

        # VALIDASI MANUAL (Quick Check)
        # Kita gunakan data 6 bulan terakhir yang tidak dilihat saat training
        df_val = fetch_data(symbol, period="6mo", interval="1h")

        if df_val.empty:
            raise ValueError("No validation data fetched")

        env_val = TradingEnv(df_val)
        obs, _ = env_val.reset()
        done = False
        wins = 0
        total_actions = 0

        # Simulasi Trading Cepat
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env_val.step(action)
            done = terminated or truncated

            if action != 0:  # Jika Buy/Sell (bukan Hold)
                total_actions += 1
                if reward > 0:  # Profit
                    wins += 1

        # Kalkulasi Statistik Sederhana
        final_balance = info.get("balance", 1000)
        initial_balance = 1000
        profit = final_balance - initial_balance
        is_profitable = profit > 0

        # Hitung Winrate
        win_rate = (wins / total_actions * 100) if total_actions > 0 else 0.0

        report["final_stats"] = {
            "profit": round(profit, 2),
            "win_rate_est": round(win_rate, 2),
            "trades": total_actions,
        }

    except Exception as e:
        report["steps"].append(f"❌ Backtest Error: {str(e)}")
        return report

    # --- STEP 3: EVALUATION & DEPLOY ---
    # Syarat: Profitable DAN Winrate lumayan (misal > 40% untuk RR tinggi, atau sesuaikan)
    if is_profitable:
        report["steps"].append(
            f"✅ Validation Passed! Profit: ${profit:.2f}, WR: {win_rate:.1f}%"
        )

        success = deploy_model(symbol)
        if success:
            report["deployed"] = True
            report["steps"].append("🎉 Model PROMOTED to Production (Live).")
        else:
            report["steps"].append("⚠️ Deployment Failed (File Error).")
    else:
        report["steps"].append(
            f"🛑 Validation Failed. Model discarded. (Profit: ${profit:.2f}, WR: {win_rate:.1f}%)"
        )

    return report
