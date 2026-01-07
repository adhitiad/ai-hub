import pandas as pd
from fastapi import APIRouter, Depends

from src.api.auth import get_current_user
from src.core.database import fix_id, signals_collection

router = APIRouter(prefix="/journal", tags=["Trading Journal & Analytics"])


@router.get("/history")
async def get_trade_history(limit: int = 50, user: dict = Depends(get_current_user)):
    """
    Mengambil riwayat trading yang sudah selesai (WIN/LOSS).
    """
    # Ambil sinyal yang statusnya sudah 'WIN' atau 'LOSS'
    # (Asumsi watcher.py mengupdate status signal di DB)
    cursor = (
        signals_collection.find({"status": {"$in": ["WIN", "LOSS"]}})
        .sort("closed_at", -1)
        .limit(limit)
    )

    trades = await cursor.to_list(length=limit)
    return [fix_id(t) for t in trades]


@router.get("/stats")
async def get_trading_stats(user: dict = Depends(get_current_user)):
    """
    Menghitung Win Rate, Profit Factor, dan Drawdown secara otomatis.
    """
    # 1. Ambil semua trade yang selesai
    cursor = signals_collection.find({"status": {"$in": ["WIN", "LOSS"]}})
    trades = await cursor.to_list(length=1000)

    if not trades:
        return {
            "win_rate": 0,
            "profit_factor": 0,
            "total_trades": 0,
            "net_pnl": 0,
            "max_drawdown": 0,
        }

    # 2. Konversi ke Pandas DataFrame untuk perhitungan mudah
    df = pd.DataFrame(trades)

    # Pastikan ada kolom PnL (Watcher harus menyimpan nominal profit/loss)
    # Jika watcher menyimpan dalam 'pips', kita konversi estimasi ke currency
    if "pnl_currency" not in df.columns:
        # Fallback dummy logic jika kolom belum ada
        df["pnl_currency"] = df.apply(
            lambda x: 100000 if x["status"] == "WIN" else -50000, axis=1
        )

    # --- HITUNG STATISTIK ---

    # A. Win Rate
    total_trades = len(df)
    wins = len(df[df["status"] == "WIN"])
    win_rate = (wins / total_trades) * 100

    # B. Profit Factor (Gross Profit / Gross Loss)
    gross_profit = df[df["pnl_currency"] > 0]["pnl_currency"].sum()
    gross_loss = abs(df[df["pnl_currency"] < 0]["pnl_currency"].sum())
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 999

    # C. Max Drawdown
    df["cumulative_pnl"] = df["pnl_currency"].cumsum()
    df["peak"] = df["cumulative_pnl"].cummax()
    df["drawdown"] = df["cumulative_pnl"] - df["peak"]
    max_drawdown = df["drawdown"].min()

    # D. Risk : Reward Rata-rata
    avg_win = df[df["pnl_currency"] > 0]["pnl_currency"].mean()
    avg_loss = abs(df[df["pnl_currency"] < 0]["pnl_currency"].mean())
    risk_reward = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0

    return {
        "total_trades": total_trades,
        "win_rate": f"{round(win_rate, 1)}%",
        "profit_factor": profit_factor,
        "avg_risk_reward": f"1:{risk_reward}",
        "net_pnl": df["pnl_currency"].sum(),
        "max_drawdown": max_drawdown,
        "equity_curve": df["cumulative_pnl"].tolist(),  # Untuk chart di frontend
    }
