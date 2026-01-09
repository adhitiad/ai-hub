from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import get_current_user
from src.core.backtest_engine import run_backtest_simulation

router = APIRouter(prefix="/backtest", tags=["Backtest Playground"])


@router.get("/run")
async def run_backtest(
    symbol: str,
    period: str = "2y",
    balance: int = 100000000,
    user: dict = Depends(get_current_user),
):
    """
    Menjalankan simulasi strategi AI pada data historis.
    Contoh: /backtest/run?symbol=BBCA.JK&period=6mo
    """
    # Validasi input
    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y"]
    if period not in valid_periods:
        raise HTTPException(400, f"Period harus salah satu dari {valid_periods}")

    try:
        # Panggil Engine (Synchronous tapi cepat karena hanya inference)
        result = run_backtest_simulation(symbol, period, balance)

        if "error" in result:
            raise HTTPException(400, result["error"])

        return result

    except Exception as e:
        raise HTTPException(500, f"Backtest Error: {str(e)}")
