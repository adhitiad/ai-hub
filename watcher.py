import asyncio  # Pastikan ada
from datetime import datetime

import pandas as pd
import pytz
import yfinance as yf

from src.core.database import alerts_collection, signals_collection
from src.core.logger import logger
from src.core.news_collector import analyze_news_sentiment, fetch_market_news

# CONFIG BIAYA (Simulasi Real Market)
SPREAD_PIPS = 2  # Spread rata-rata (Forex)
COMMISSION_PCT = 0.1  # Komisi Saham (0.1% per transaksi)
COMMISSION_FX = 7.0  # Komisi Forex ($7 per lot round turn)


# Helper agar yfinance berjalan di thread terpisah (Non-blocking)
async def fetch_live_price(symbol):
    def _fetch():
        try:
            ticker = yf.Ticker(symbol)
            # Fast fetch 1 hari terakhir, 1 menit interval (lebih ringan)
            df = ticker.history(period="1d", interval="1m")
            if df.empty:
                return None
            return df.iloc[-1]
        except:
            return None

    return await asyncio.to_thread(_fetch)


# HAPUS: import requests_cache


# HAPUS: session = requests_cache...


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
                            "opened_at": datetime.utcnow(),
                            "fill_price": entry_price,  # Harga eksekusi
                        }
                    },
                )
                logger.info(f"✅ ORDER FILLED: {symbol} at {entry_price}")
                # Opsional: Kirim Notif Telegram "Order Filled"

            continue  # Lanjut ke signal berikutnya, jangan cek TP/SL dulu

        # --- LOGIKA B: HANDLE OPEN POSITIONS (TP/SL Check) ---
        # Hitung PnL Floating dengan BIAYA (Spread/Komisi)

        entry_price = sig.get("fill_price", sig["price"])
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
                            "closed_at": datetime.utcnow(),
                            "exit_price": exit_price,
                            "exit_reason": exit_reason,
                            "pnl": pnl_net,  # Simpan Net PnL (Realistis)
                        }
                    },
                )
                logger.info(f"🏁 TRADE CLOSED {symbol}: {final_status} ({pnl_net:.2f})")


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
                "CLOSE": last_row["Close"],
                "RSI": last_row.get("RSI_14", 50),
                "VOLUME": last_row["Volume"],
                "SMA20": last_row.get("SMA_20", 0),
            }
            try:
                condition_str = alert["condition"].upper()
                for k, v in safe_env.items():
                    condition_str = condition_str.replace(k, str(v))

                if eval(condition_str):
                    triggered = True
            except:
                pass

        if triggered:
            logger.info(f"🚨 ALERT TRIGGERED: {symbol} - {alert['note']}")
            await alerts_collection.update_one(
                {"_id": alert["_id"]},
                {
                    "$set": {
                        "status": "TRIGGERED",
                        "triggered_at": datetime.utcnow(),  # Ini juga sebaiknya pakai ()
                    }
                },
            )


async def run_watcher():
    logger.info("🚀 AI TRADING WATCHER (MongoDB Version) STARTED")
    while True:
        await check_positions()
        # Cek setiap 30 detik
        await asyncio.sleep(30)


if __name__ == "__main__":
    try:
        asyncio.run(run_watcher())
    except KeyboardInterrupt:
        logger.info("Watcher stopped manually.")
