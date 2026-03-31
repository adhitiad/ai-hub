# src/core/whale_crypto.py

import asyncio

import ccxt.async_support as ccxt  # Gunakan versi Async!
import pandas as pd

from src.core.logger import logger

# Config Threshold Paus (dalam USD/USDT)
WHALE_THRESHOLD = 10000  # Transaksi > $10k dianggap Paus Kecil/Sedang
EXCHANGE_LIST = ["binance", "bybit", "gateio", "mexc", "okx", "kucoin"]


async def analyze_crypto_whales(symbol: str):
    """
    Menganalisis pergerakan Paus di pasar Spot Crypto.
    Logika: Menghitung Net Volume dari transaksi besar (Aggressive Buys vs Sells).
    Mendukung agregasi data dari semua exchange secara concurrent.
    """

    async def _close_exchange(exchange):
        if not exchange:
            return
        try:
            await exchange.close()
        except Exception:
            pass
        session = getattr(exchange, "session", None)
        if session:
            try:
                await session.close()
            except Exception:
                pass

    async def _fetch_and_process(ex_name):
        exchange = None
        try:
            exchange_class = getattr(ccxt, ex_name)
            exchange = exchange_class({"enableRateLimit": True})
            trades = await exchange.fetch_trades(symbol, limit=1000)

            if not trades:
                await _close_exchange(exchange)
                return 0.0, 0.0

            df = pd.DataFrame(trades)
            df["cost"] = df["price"] * df["amount"]

            whale_trades = df[df["cost"] >= WHALE_THRESHOLD].copy()

            if whale_trades.empty:
                await _close_exchange(exchange)
                return 0.0, 0.0

            buy_vol = float(whale_trades[whale_trades["side"] == "buy"]["cost"].sum())
            sell_vol = float(whale_trades[whale_trades["side"] == "sell"]["cost"].sum())

            await _close_exchange(exchange)
            return buy_vol, sell_vol

        except Exception as e:
            logger.error("Whale Analysis Error (%s on %s): %s", symbol, ex_name, e)
            await _close_exchange(exchange)
            return 0.0, 0.0

    tasks = [_fetch_and_process(ex_name) for ex_name in EXCHANGE_LIST]
    results = await asyncio.gather(*tasks)

    total_buy_vol = sum(res[0] for res in results)
    total_sell_vol = sum(res[1] for res in results)

    if total_buy_vol == 0 and total_sell_vol == 0:
        return {
            "action": "NEUTRAL",
            "score": 0,
            "reason": "No whale activity found across exchanges",
            "exchange": "aggregated",
        }

    total_vol = total_buy_vol + total_sell_vol
    net_flow = total_buy_vol - total_sell_vol

    whale_score = (net_flow / total_vol) * 100 if total_vol > 0 else 0

    action = "NEUTRAL"
    reason = f"Whale Flow: {whale_score:.1f}%"

    if whale_score > 20:
        action = "BUY"
        reason = f"🐳 Whales Accumulating (+${net_flow / 1000:.1f}k)"
    elif whale_score < -20:
        action = "SELL"
        reason = f"🐋 Whales Dumping (-${abs(net_flow) / 1000:.1f}k)"

    return {
        "action": action,
        "score": whale_score,
        "buy_vol": total_buy_vol,
        "sell_vol": total_sell_vol,
        "reason": reason,
        "exchange": "aggregated",
    }


# Test Runner (Optional)
if __name__ == "__main__":

    async def main():
        res = await analyze_crypto_whales("BTC/USDT")
        print(res)

    asyncio.run(main())
