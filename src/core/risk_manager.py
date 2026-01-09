from datetime import datetime

from src.core.database import signals_collection, users_collection
from src.core.logger import logger

# Config Hardcoded (Bisa dipindah ke Database/User Settings nanti)
MAX_DAILY_LOSS_PERCENT = 0.05  # Max rugi 5% dari saldo per hari
MAX_CONSECUTIVE_LOSSES = 5  # Stop jika rugi 5x berturut-turut


async def check_circuit_breaker(user_balance=1000):
    """
    Mengecek apakah trading harus dihentikan sementara karena risiko tinggi.
    Return: (boleh_trading: bool, alasan: str)
    """
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())

    # 1. Ambil Trade Hari Ini yang LOSS
    cursor = signals_collection.find(
        {"status": "LOSS", "closed_at": {"$gte": today_start}}
    )

    daily_loss_amount = 0
    loss_count = 0

    # Ambil 10 trade terakhir untuk cek loss streak
    recent_cursor = (
        signals_collection.find({"status": {"$in": ["WIN", "LOSS"]}})
        .sort("closed_at", -1)
        .limit(10)
    )
    recent_trades = await recent_cursor.to_list(length=10)

    # Hitung Total Kerugian Hari Ini
    async for trade in cursor:
        # PnL biasanya disimpan dalam currency value di field 'pnl_currency' atau estimasi dari pips
        # Kita asumsikan ada field 'pnl_amount' (jika belum ada, kita pakai pips * lot estimasi)
        pnl = trade.get("pnl_amount", 0)
        if pnl == 0:
            # Fallback sederhana: Asumsi 1 pip = $10 (Standard) * Lot
            pnl = abs(trade.get("pips", 0)) * trade.get("lot_size_num", 0.1) * 10

        daily_loss_amount += abs(pnl)

    # 2. Cek Limit Harian (5% Balance)
    max_loss_limit = user_balance * MAX_DAILY_LOSS_PERCENT
    if daily_loss_amount >= max_loss_limit:
        msg = f"🛑 CIRCUIT BREAKER TRIPPED: Daily Loss ${daily_loss_amount:.2f} > Limit ${max_loss_limit:.2f}"
        logger.warning(msg)
        return False, msg

    # 3. Cek Loss Streak (Berturut-turut)
    consecutive_loss = 0
    for t in recent_trades:
        if t["status"] == "LOSS":
            consecutive_loss += 1
        else:
            break  # Reset jika ketemu WIN

    if consecutive_loss >= MAX_CONSECUTIVE_LOSSES:
        msg = f"🛑 CIRCUIT BREAKER TRIPPED: {consecutive_loss} Consecutive Losses"
        logger.warning(msg)
        return False, msg

    return True, "OK"
