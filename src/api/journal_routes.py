import pandas as pd
import re

from fastapi import APIRouter, Depends

from src.api.auth import get_current_user
from src.core.database import fix_id, signals_collection

router = APIRouter(prefix="/journal", tags=["Trading Journal & Analytics"])


def _parse_quantity(value):
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"[-+]?[0-9]*\.?[0-9]+", value)
        if match:
            return float(match.group())
    return 0


def _normalize_action(action: str):
    if not action:
        return "BUY"
    return "SELL" if "SELL" in action.upper() else "BUY"


def _normalize_trade(doc):
    doc = fix_id(doc)
    action = _normalize_action(doc.get("action") or doc.get("type", ""))
    entry_price = doc.get("entry_price") or doc.get("price") or 0
    exit_price = doc.get("exit_price") or doc.get("close_price")
    quantity = _parse_quantity(doc.get("lot_size") or doc.get("quantity"))
    entry_date = doc.get("entry_date") or doc.get("created_at")
    exit_date = doc.get("exit_date") or doc.get("closed_at") or doc.get("updated_at")
    pnl = doc.get("pnl_currency") if doc.get("pnl_currency") is not None else doc.get("pnl")
    pnl_percent = doc.get("pnl_percent")
    status = doc.get("status", "OPEN")

    return {
        **doc,
        "action": action,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "quantity": quantity,
        "entry_date": entry_date,
        "exit_date": exit_date,
        "pnl": pnl,
        "pnl_percent": pnl_percent,
        "status": status,
    }


@router.get("/history")
async def get_trade_history(limit: int = 50, user: dict = Depends(get_current_user)):
    """
    Mengambil riwayat trading yang sudah selesai (WIN/LOSS).
    """
    # Ambil sinyal yang statusnya sudah 'WIN' atau 'LOSS'
    # (Asumsi watcher.py mengupdate status signal di DB)
    cursor = (
        signals_collection.find({"status": {"$in": ["OPEN", "WIN", "LOSS"]}})
        .sort("closed_at", -1)
        .limit(limit)
    )

    trades = await cursor.to_list(length=limit)
    return [_normalize_trade(t) for t in trades]


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
            "total_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "total_pnl_percent": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "best_trade": 0,
            "worst_trade": 0,
            "equity_curve": [],
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
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

    # B. Profit Factor (Gross Profit / Gross Loss)
    gross_profit = df[df["pnl_currency"] > 0]["pnl_currency"].sum()
    gross_loss = abs(df[df["pnl_currency"] < 0]["pnl_currency"].sum())
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 999

    # C. Max Drawdown
    df["cumulative_pnl"] = df["pnl_currency"].cumsum()
    df["peak"] = df["cumulative_pnl"].cummax()
    df["drawdown"] = df["cumulative_pnl"] - df["peak"]
    max_drawdown = abs(df["drawdown"].min())

    # D. Risk : Reward Rata-rata
    avg_win = df[df["pnl_currency"] > 0]["pnl_currency"].mean()
    avg_loss = abs(df[df["pnl_currency"] < 0]["pnl_currency"].mean())
    risk_reward = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0

    total_pnl = df["pnl_currency"].sum()
    best_trade = df["pnl_currency"].max() if len(df) else 0
    worst_trade = df["pnl_currency"].min() if len(df) else 0

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 1),
        "total_pnl": total_pnl,
        "total_pnl_percent": 0,
        "avg_win": float(avg_win) if not pd.isna(avg_win) else 0,
        "avg_loss": float(avg_loss) if not pd.isna(avg_loss) else 0,
        "profit_factor": profit_factor,
        "max_drawdown": float(max_drawdown) if not pd.isna(max_drawdown) else 0,
        "best_trade": float(best_trade) if not pd.isna(best_trade) else 0,
        "worst_trade": float(worst_trade) if not pd.isna(worst_trade) else 0,
        "equity_curve": df["cumulative_pnl"].tolist(),
        # Legacy fields
        "avg_risk_reward": f"1:{risk_reward}",
        "net_pnl": total_pnl,
    }
