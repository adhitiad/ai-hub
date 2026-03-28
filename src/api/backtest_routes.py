import traceback

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import get_current_user
from src.core.backtest_engine import run_backtest_simulation
from src.core.logger import logger

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
    Contoh: /backtest/run?symbol=BBCA.JK&period=2y
    """
    # Validasi input
    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]
    if period not in valid_periods:
        raise HTTPException(400, f"Period harus salah satu dari {valid_periods}")

    try:
        result = await run_backtest_simulation(symbol, period, balance)

        if result.get("error"):
            err_msg = result["error"]
            # Model belum dilatih → 503 Service Unavailable
            if "belum dilatih" in err_msg:
                raise HTTPException(
                    status_code=503,
                    detail=f"Model AI belum tersedia untuk simbol ini. {err_msg}",
                )
            # Aset tidak terdaftar → 404
            if "tidak terdaftar" in err_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"Aset tidak dikenal: {err_msg}",
                )
            raise HTTPException(status_code=400, detail=err_msg)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Backtest Error for %s: %s", symbol, e)
        logger.error(traceback.format_exc())
        raise HTTPException(500, "Backtest Error: %s" % e) from e
