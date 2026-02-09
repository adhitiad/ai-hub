import asyncio
from datetime import datetime, timezone

from src.core.database import signals_collection
from src.core.logger import logger


class RiskManager:
    """
    Penjaga Gawang (Safety Guard).
    Mencegah bot terus-terusan trading saat performa sedang buruk (Drawdown).
    """

    def __init__(self):
        # Config Hardcoded (Bisa dipindah ke .env nanti)
        self.MAX_DAILY_LOSS_PERCENT: float = (
            0.05  # Stop jika rugi 5% dari saldo per hari
        )
        self.MAX_CONSECUTIVE_LOSSES: int = 5  # Stop jika rugi 5x berturut-turut
        self.SYSTEM_BALANCE: float = 1000  # Asumsi Balance Virtual System ($1000)

    async def can_trade(self) -> tuple[bool, str]:
        """
        Public API untuk mengecek apakah boleh trading.
        Returns: (bool, str) -> (allowed, reason)
        """
        allowed, reason = await self._check_circuit_breaker()
        if not allowed:
            logger.warning(f"⛔ RISK MANAGER: Trading Halted! Reason: {reason}")
        return allowed, reason

    async def _check_circuit_breaker(self):
        return await check_circuit_breaker(
            balance=self.SYSTEM_BALANCE,
            max_daily_loss_percent=self.MAX_DAILY_LOSS_PERCENT,
            max_consecutive_losses=self.MAX_CONSECUTIVE_LOSSES,
        )


# --- GLOBAL INSTANCE ---
# Ini yang akan di-import oleh producer.py
risk_manager = RiskManager()


async def check_circuit_breaker(
    balance: float,
    max_daily_loss_percent: float = 0.05,
    max_consecutive_losses: int = 5,
):
    """
    Pengecekan batas kerugian.
    Return: (bool, str) -> (Allowed, Reason)
    """
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # 1. Hitung Kerugian Hari Ini
    cursor = signals_collection.find(
        {"status": "LOSS", "closed_at": {"$gte": today_start}}
    )
    daily_trades = await cursor.to_list(length=1000)

    daily_loss_amount = 0.0
    for trade in daily_trades:
        pnl = trade.get("pnl", trade.get("pnl_amount", 0))
        if pnl == 0 and "pips" in trade and "lot_size_num" in trade:
            pnl = trade.get("pips", 0) * trade.get("lot_size_num", 0) * 10
        if pnl == 0:
            pnl = -5.0
        daily_loss_amount += abs(pnl)

    max_loss_limit = balance * max_daily_loss_percent
    if daily_loss_amount >= max_loss_limit:
        return (
            False,
            f"CIRCUIT BREAKER TRIPPED: Daily Loss ${daily_loss_amount:.2f} > Limit ${max_loss_limit:.2f}",
        )

    # 2. Cek Loss Streak (Berturut-turut)
    recent_cursor = (
        signals_collection.find({"status": {"$in": ["WIN", "LOSS"]}})
        .sort("closed_at", -1)
        .limit(10)
    )
    recent_trades = await recent_cursor.to_list(length=10)

    consecutive_loss = 0
    for trade in recent_trades:
        if trade.get("status") == "LOSS":
            consecutive_loss += 1
        else:
            break

    if consecutive_loss >= max_consecutive_losses:
        return False, f"Hit {consecutive_loss} Consecutive Losses"

    return True, "OK"
