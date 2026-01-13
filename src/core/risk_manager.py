import asyncio
from datetime import datetime

from src.core.database import signals_collection
from src.core.logger import logger


class RiskManager:
    """
    Penjaga Gawang (Safety Guard).
    Mencegah bot terus-terusan trading saat performa sedang buruk (Drawdown).
    """

    def __init__(self):
        # Config Hardcoded (Bisa dipindah ke .env nanti)
        self.MAX_DAILY_LOSS_PERCENT = 0.05  # Stop jika rugi 5% dari saldo per hari
        self.MAX_CONSECUTIVE_LOSSES = 5  # Stop jika rugi 5x berturut-turut
        self.SYSTEM_BALANCE = 1000  # Asumsi Balance Virtual System ($1000)

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
        """
        Logic internal pengecekan batas kerugian.
        Return: (bool, str) -> (Allowed, Reason)
        """
        today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())

        # 1. Hitung Kerugian Hari Ini
        # Cari semua signal yang ditutup hari ini dengan status LOSS
        cursor = signals_collection.find(
            {"status": "LOSS", "closed_at": {"$gte": today_start}}
        )

        daily_loss_amount = 0

        async for trade in cursor:
            # PnL Real (jika ada) atau Estimasi dari Pips
            pnl = trade.get("pnl", 0)

            # Jika pnl tidak tersimpan, estimasi kasar:
            # Loss biasanya negatif, kita ambil absolutnya
            if pnl == 0:
                # Fallback: Misal rugi rata-rata $5 per trade kalau data kosong
                pnl = -5.0

            # Kita jumlahkan kerugiannya (dibuat positif untuk perbandingan limit)
            daily_loss_amount += abs(pnl)

        # Cek Limit Harian
        max_loss_limit = self.SYSTEM_BALANCE * self.MAX_DAILY_LOSS_PERCENT
        if daily_loss_amount >= max_loss_limit:
            return (
                False,
                f"Daily Loss ${daily_loss_amount:.2f} > Limit ${max_loss_limit:.2f}",
            )

        # 2. Cek Loss Streak (Berturut-turut)
        # Ambil 10 trade terakhir yang sudah selesai (WIN/LOSS)
        recent_cursor = (
            signals_collection.find({"status": {"$in": ["WIN", "LOSS"]}})
            .sort("closed_at", -1)
            .limit(10)
        )
        recent_trades = await recent_cursor.to_list(length=10)

        consecutive_loss = 0
        for t in recent_trades:
            if t["status"] == "LOSS":
                consecutive_loss += 1
            else:
                break  # Reset streak jika ketemu WIN

        if consecutive_loss >= self.MAX_CONSECUTIVE_LOSSES:
            return False, f"Hit {consecutive_loss} Consecutive Losses"

        return True, "OK"


# --- GLOBAL INSTANCE ---
# Ini yang akan di-import oleh producer.py
risk_manager = RiskManager()
