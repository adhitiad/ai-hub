from datetime import datetime, timezone

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from src.api.auth import get_current_user
from src.core.bandarmology import Bandarmology
from src.core.data_loader import fetch_data
from src.core.forex_engine import ForexEngine
from src.core.whale_crypto import analyze_crypto_whales

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


@router.get("/chart/{symbol:path}")
def get_advanced_chart_data(
    symbol: str, timeframe: str = "1h", user: dict = Depends(get_current_user)
):
    """
    Return OHLCV + Indicators + Bandar Line untuk charting frontend (TradingView/Lightweight Charts).
    """
    import urllib.parse

    decoded_symbol = urllib.parse.unquote(symbol)
    period_map = {"1d": "1y", "1h": "1mo", "15m": "5d"}
    period = period_map.get(timeframe, "2y")

    try:
        df = fetch_data(decoded_symbol, period=period, interval=timeframe)

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


def _format_usd(value: float) -> str:
    sign = "+" if value >= 0 else "-"
    abs_val = abs(value)
    if abs_val >= 1_000_000:
        return f"{sign}${abs_val/1_000_000:.1f}M"
    if abs_val >= 1_000:
        return f"{sign}${abs_val/1_000:.1f}k"
    return f"{sign}${abs_val:.0f}"


@router.get("/crypto/summary")
async def get_crypto_summary(
    symbol: str = "BTC/USDC", user: dict = Depends(get_current_user)
):

    try:
        whale = await analyze_crypto_whales(symbol)
        score = float(whale.get("score", 0))
        fear_greed = max(0, min(100, round(50 + (score / 2), 1)))
        buy_vol = float(whale.get("buy_vol", 0))
        sell_vol = float(whale.get("sell_vol", 0))
        net_flow = buy_vol - sell_vol

        return {
            "symbol": symbol,
            "fear_greed": fear_greed,
            "net_flow": _format_usd(net_flow),
            "action": whale.get("action", "NEUTRAL"),
            "score": round(score, 1),
            "exchange": whale.get("exchange", ""),
            "timestamp": datetime.now(timezone.utc),
        }
    except Exception:
        return {
            "symbol": symbol,
            "fear_greed": 50,
            "net_flow": "+$0",
            "action": "NEUTRAL",
            "score": 0,
            "exchange": "",
            "timestamp": datetime.now(timezone.utc),
        }


@router.get("/bandar/{symbol}")
def get_bandar_summary(symbol: str, user: dict = Depends(get_current_user)):
    df = fetch_data(symbol, period="3mo", interval="1d")
    result = (
        Bandarmology.analyze_bandar_flow(df)
        if not df.empty
        else {
            "status": "NEUTRAL",
            "score": 0,
            "message": "No data",
            "vol_ratio": 0,
        }
    )
    return {
        "symbol": symbol,
        "status": result.get("status", "NEUTRAL"),
        "score": result.get("score", 0),
        "message": result.get("message", ""),
        "vol_ratio": result.get("vol_ratio", 0),
    }


@router.get("/forex/summary")
async def get_forex_summary(
    pair: str = "USDJPY", user: dict = Depends(get_current_user)
):
    forex = ForexEngine()
    data = forex.analyze_strength(pair.upper())
    strengths = data.get("strength_meter", {})

    return {
        "pair": pair.upper(),
        "base_currency": pair[:3].upper(),
        "quote_currency": pair[3:].upper(),
        "strength": strengths,
        "signal": data.get("signal", "NEUTRAL"),
        "session": data.get("session", ""),
        "timestamp": datetime.now(timezone.utc),
    }
