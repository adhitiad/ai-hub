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
    """
    for ex_name in EXCHANGE_LIST:
        exchange = None
        try:
            exchange_class = getattr(ccxt, ex_name)
            # enableRateLimit wajib agar tidak kena ban IP
            exchange = exchange_class({"enableRateLimit": True})

            # 1. Fetch Recent Trades (Transaksi yang baru saja terjadi)
            # Limit 1000 transaksi terakhir
            trades = await exchange.fetch_trades(symbol, limit=1000)

            if not trades:
                await exchange.close()
                continue

            # 2. Proses Data
            df = pd.DataFrame(trades)
            df["cost"] = df["price"] * df["amount"]

            # 3. Filter Transaksi Paus (Hanya yang > Threshold)
            whale_trades = df[df["cost"] >= WHALE_THRESHOLD].copy()

            if whale_trades.empty:
                await exchange.close()
                continue

            # 4. Hitung Buy vs Sell Volume Paus
            # 'side' = 'buy' berarti Taker BUY (Agresif Beli)
            # 'side' = 'sell' berarti Taker SELL (Agresif Jual/Guyur)
            buy_vol = whale_trades[whale_trades["side"] == "buy"]["cost"].sum()
            sell_vol = whale_trades[whale_trades["side"] == "sell"]["cost"].sum()

            total_vol = buy_vol + sell_vol
            net_flow = buy_vol - sell_vol

            # 5. Tentukan Sinyal
            # Score skala -100 sampai 100
            whale_score = (net_flow / total_vol) * 100 if total_vol > 0 else 0

            action = "NEUTRAL"
            reason = f"Whale Flow: {whale_score:.1f}%"

            if whale_score > 20:
                action = "BUY"
                reason = f"🐳 Whales Accumulating (+${net_flow/1000:.1f}k)"
            elif whale_score < -20:
                action = "SELL"
                reason = f"🐋 Whales Dumping (-${abs(net_flow)/1000:.1f}k)"

            await exchange.close()
            return {
                "action": action,
                "score": whale_score,
                "buy_vol": buy_vol,
                "sell_vol": sell_vol,
                "reason": reason,
                "exchange": ex_name,
            }

        except Exception as e:
            logger.error(f"Whale Analysis Error ({symbol} on {ex_name}): {e}")
            if exchange:
                try:
                    await exchange.close()
                except:
                    pass
            continue

    return {"action": "NEUTRAL", "score": 0, "reason": "No exchange available"}


# Test Runner (Optional)
if __name__ == "__main__":

    async def main():
        res = await analyze_crypto_whales("BTC/USDT")
        print(res)

    asyncio.run(main())
