import numpy as np
from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import get_current_user
from src.core.bandarmology import analyze_bandar_flow
from src.core.data_loader import fetch_data

router = APIRouter(prefix="/market", tags=["Market Data & Charts"])


from src.core.agent import ai_agent


@router.post("/get-signal")
async def get_signal(data):
    decision = ai_agent.get_action(
        {
            "close_scaled": data.normalized_price,
            "rsi": data.rsi,
            "macd": data.macd,
            "bandar_score": data.bandar_accum,
            "volatility": data.atr,
            "has_position": 0,
        }
    )
    return decision
    # Output: {"action": "BUY", "reason": "AI PPO Policy..."}


@router.get("/chart/{symbol}")
def get_advanced_chart_data(
    symbol: str, timeframe: str = "1h", user: dict = Depends(get_current_user)
):
    """
    Return OHLCV + Indicators + Bandar Line untuk charting frontend (TradingView/Lightweight Charts).
    """
    period_map = {"1d": "1y", "1h": "1mo", "15m": "5d"}
    period = period_map.get(timeframe, "2y")

    try:
        df = fetch_data(symbol, period=period, interval=timeframe)

        # Tambahan Indicator Khusus Chart
        # Misal: Garis Akumulasi Bandar (Custom Line)
        # Logika simpel: Jika Vol naik & Harga naik = Akumulasi (+Volume), sebaliknya Distribusi (-Volume)
        df["Bandar_Vol"] = np.where(
            df["Close"] > df["Open"], df["Volume"], -df["Volume"]
        )
        df["Bandar_Accumulation"] = df["Bandar_Vol"].cumsum()  # Cumulative Line

        # Format Data untuk Frontend (JSON Array)
        chart_data = []
        for index, row in df.iterrows():
            chart_data.append(
                {
                    "time": str(index),  # Frontend butuh timestamp/string
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                    # Indicators
                    "sma20": row.get("SMA_20"),
                    "sma50": row.get("SMA_50"),
                    "rsi": row.get("RSI_14"),
                    "bandar_accum": row.get("Bandar_Accumulation"),
                }
            )

        return {"symbol": symbol, "data": chart_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/depth/{symbol}")
def get_market_depth(symbol: str, user: dict = Depends(get_current_user)):
    """
    Detail Bid/Offer.
    NOTE: YFinance TIDAK menyediakan live orderbook Level 2.
    Ini adalah struktur JSON standar jika Anda menyambungkan ke API Broker/GoAPI.
    """

    # MOCK DATA (Karena yfinance tidak support level 2)
    # Anda perlu replace ini dengan API Call ke Data Provider Real-time
    import random

    base_price = 1000  # Dummy

    # Simulasi Orderbook
    bids = [
        {"price": base_price - (i * 5), "vol": random.randint(100, 5000)}
        for i in range(1, 6)
    ]
    offers = [
        {"price": base_price + (i * 5), "vol": random.randint(100, 5000)}
        for i in range(1, 6)
    ]

    return {
        "symbol": symbol,
        "status": "MOCK_DATA (Connect Real Broker API)",
        "bids": bids,  # Antrian Beli
        "offers": offers,  # Antrian Jual
    }
