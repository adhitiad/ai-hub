import asyncio  # Pastikan ada
from datetime import datetime, timezone

import pandas as pd
import pytz
import yfinance as yf

import ccxt.async_support as ccxt

from src.core.logger import logger
from src.database.database import alerts_collection, signals_collection
from src.core.formula_evaluator import safe_eval

# CONFIG BIAYA (Simulasi Real Market)
SPREAD_PIPS = 2  # Spread rata-rata (Forex)
COMMISSION_PCT = 0.1  # Komisi Saham (0.1% per transaksi)
COMMISSION_FX = 7.0  # Komisi Forex ($7 per lot round turn)


# Global Exchange Cache untuk efisiensi dan menghindari session leak
class ExchangeManager:
    def __init__(self):
        self.exchanges = {}

    async def get_exchange(self, name):
        if name not in self.exchanges:
            try:
                exchange_class = getattr(ccxt, name)
                self.exchanges[name] = exchange_class({"enableRateLimit": True})
            except Exception as e:
                logger.error(f"Failed to initialize exchange {name}: {e}")
                return None
        return self.exchanges[name]

    async def close_all(self):
        for name, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.info(f"Closed exchange connection: {name}")
            except Exception as e:
                logger.error(f"Error closing exchange {name}: {e}")
        self.exchanges.clear()

exchange_manager = ExchangeManager()


# Helper fetch harga live untuk CRYPTO via CCXT
async def _fetch_crypto_price(symbol):
    """Fetch OHLCV terbaru untuk crypto pair (e.g. CKB/USDC) via CCXT cached instances."""
    EXCHANGE_LIST = ["binance", "bybit", "gateio", "mexc", "okx", "kucoin"]
    for ex_name in EXCHANGE_LIST:
        try:
            exchange = await exchange_manager.get_exchange(ex_name)
            if not exchange:
                continue
                
            ohlcv = await exchange.fetch_ohlcv(symbol, "1m", limit=2)
            if ohlcv and len(ohlcv) > 0:
                last = ohlcv[-1]  # [timestamp, open, high, low, close, volume]
                return {
                    "Close": last[4],
                    "High": last[2],
                    "Low": last[3],
                }
        except Exception:
            pass
    return None


# Helper fetch harga live untuk SAHAM/FOREX via yfinance
async def _fetch_yf_price(symbol):
    def _fetch():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval="1m")
            if df.empty:
                return None
            return df.iloc[-1]
        except Exception:
            return None
    return await asyncio.to_thread(_fetch)


async def fetch_live_price(symbol):
    """Smart Price Fetcher: CCXT untuk crypto ('/'), yfinance untuk saham/forex."""
    if "/" in symbol:
        result = await _fetch_crypto_price(symbol)
        return result  # dict {Close, High, Low} atau None
    else:
        row = await _fetch_yf_price(symbol)
        if row is None:
            return None
        # Kembalikan sebagai dict agar format sama
        return {
            "Close": float(row["Close"]),
            "High": float(row["High"]),
            "Low": float(row["Low"]),
        }


async def check_positions():
    """
    Looping mengecek semua sinyal 'OPEN' di Database MongoDB.
    Jika harga menyentuh SL/TP, status diupdate jadi WIN/LOSS.
    """
    logger.info("👀 Watcher Loop Started...")

    # 1. Ambil semua sinyal yang statusnya masih OPEN
    cursor = signals_collection.find({"status": {"$in": ["OPEN", "PENDING"]}})
    active_signals = await cursor.to_list(length=1000)

    if not active_signals:
        return

    print(f"Checking {len(active_signals)} active positions...")

    for sig in active_signals:
        symbol = sig["symbol"]

        # --- PERBAIKAN: Gunakan Async Fetch ---
        curr = await fetch_live_price(symbol)

        if curr is None:
            continue

        current_price = curr["Close"]
        high_price = curr["High"]
        low_price = curr["Low"]

        # --- LOGIKA A: HANDLE PENDING ORDER (LIMIT/STOP) ---
        if sig["status"] == "PENDING":
            entry_price = sig["price"]  # Harga Limit yang diinginkan
            action = sig["action"]  # BUY LIMIT / SELL LIMIT

            triggered = False

            # Cek apakah harga pasar sudah menjemput order limit kita
            if "BUY" in action and low_price <= entry_price:
                triggered = True
            elif "SELL" in action and high_price >= entry_price:
                triggered = True

            if triggered:
                # Update jadi OPEN (Aktif)
                await signals_collection.update_one(
                    {"_id": sig["_id"]},
                    {
                        "$set": {
                            "status": "OPEN",
                            "opened_at": datetime.now(timezone.utc),
                            "fill_price": entry_price,  # Harga eksekusi
                        }
                    },
                )
                logger.info("✅ ORDER FILLED: %s at %s", symbol, entry_price)
                # Opsional: Kirim Notif Telegram "Order Filled"

            continue  # Lanjut ke signal berikutnya, jangan cek TP/SL dulu

        # --- LOGIKA B: HANDLE OPEN POSITIONS (TP/SL Check) ---
        # Hitung PnL Floating dengan BIAYA (Spread/Komisi)

        entry_price = (
            sig.get("fill_price") or sig.get("price") or sig.get("entry_price")
        )
        if entry_price is None:
            logger.warning(
                "⚠️ Skipping %s: no entry price found (fill_price/price/entry_price missing)",
                symbol,
            )
            continue
        lot_size = sig.get("lot_size_num", 0.01)
        asset_type = sig.get("asset_type", "forex")

        pnl_gross = 0
        if "BUY" in sig["action"]:
            pnl_gross = current_price - entry_price
        else:  # SELL
            pnl_gross = entry_price - current_price

        # Konversi ke USD/IDR Value
        if asset_type == "stock_indo":
            # Saham: (Selisih * Lot * 100) - Komisi
            val_gross = pnl_gross * lot_size * 100
            commission = (entry_price * lot_size * 100) * (COMMISSION_PCT / 100)
            pnl_net = val_gross - (commission * 2)  # Komisi Beli + Jual
        else:
            # Forex: (Selisih / PipScale) * (Lot * ContractSize) - Komisi - Spread
            # Simplifikasi estimasi USD
            pip_val = 10  # Standard Lot ($10/pip)
            pnl_pips = pnl_gross * 10000  # Asumsi pair 4 digit
            pnl_net = (pnl_pips * lot_size * 10) - (COMMISSION_FX * lot_size)

            # Cek TP / SL
            tp_hit = False
            sl_hit = False
            exit_price = current_price
            exit_reason = ""

            if "BUY" in sig["action"]:
                if high_price >= sig["tp"]:
                    tp_hit = True
                    exit_price = sig["tp"]
                    exit_reason = "TP Hit"
                elif low_price <= sig["sl"]:
                    sl_hit = True
                    exit_price = sig["sl"]
                    exit_reason = "SL Hit"
            else:  # SELL
                if low_price <= sig["tp"]:
                    tp_hit = True
                    exit_price = sig["tp"]
                    exit_reason = "TP Hit"
                elif high_price >= sig["sl"]:
                    sl_hit = True
                    exit_price = sig["sl"]
                    exit_reason = "SL Hit"

            if tp_hit or sl_hit:
                final_status = "WIN" if pnl_net > 0 else "LOSS"

                await signals_collection.update_one(
                    {"_id": sig["_id"]},
                    {
                        "$set": {
                            "status": final_status,
                            "closed_at": datetime.now(timezone.utc),
                            "exit_price": exit_price,
                            "exit_reason": exit_reason,
                            "pnl": pnl_net,  # Simpan Net PnL (Realistis)
                        }
                    },
                )
                logger.info(
                    "🏁 TRADE CLOSED %s: %s (%.2f)", symbol, final_status, pnl_net
                )


async def check_alerts(df, symbol):
    # 1. Ambil semua alert aktif untuk simbol ini
    cursor = alerts_collection.find({"symbol": symbol, "status": "ACTIVE"})
    alerts = await cursor.to_list(length=100)

    if not alerts or df.empty:
        return

    last_row = df.iloc[-1]
    current_price = last_row["Close"]

    for alert in alerts:
        triggered = False

        # Cek Price Alert
        if alert["type"] == "PRICE":
            if alert["condition"] == "ABOVE" and current_price >= alert["target_price"]:
                triggered = True
            elif (
                alert["condition"] == "BELOW" and current_price <= alert["target_price"]
            ):
                triggered = True

        # Cek Formula Alert
        elif alert["type"] == "FORMULA":
            safe_env = {
                "CLOSE": float(last_row["Close"]),
                "RSI": float(last_row.get("RSI_14", 50)),
                "VOLUME": float(last_row["Volume"]),
                "SMA20": float(last_row.get("SMA_20", 0)),
            }
            if safe_eval(alert["condition"], safe_env):
                triggered = True

        if triggered:
            logger.info("🚨 ALERT TRIGGERED: %s - %s", symbol, alert["note"])
            await alerts_collection.update_one(
                {"_id": alert["_id"]},
                {
                    "$set": {
                        "status": "TRIGGERED",
                        "triggered_at": datetime.now(timezone.utc),
                    }
                },
            )


async def run_watcher():
    logger.info("🚀 AI TRADING WATCHER (MongoDB Version) STARTED")
    try:
        while True:
            await check_positions()
            # Cek setiap 30 detik
            await asyncio.sleep(30)
    finally:
        # PENTING: Tutup semua resource saat stop
        await exchange_manager.close_all()


if __name__ == "__main__":
    try:
        asyncio.run(run_watcher())
    except KeyboardInterrupt:
        logger.info("Watcher stopped manually.")
    except Exception as e:
        logger.error(f"Watcher crashed: {e}")
