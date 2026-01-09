import logging
import time

import pandas as pd
import pandas_ta as ta
import yfinance as yf

from src.core.logger import logger


def fetch_data(symbol="EURUSD=X", period="2y", interval="1h", retries=3):
    """
    Mengambil data menggunakan yf.Ticker dengan penanganan Kolom Ganda (Duplicate Columns).
    """
    for attempt in range(retries):
        try:
            # Gunakan Ticker object
            ticker = yf.Ticker(symbol)

            # Ambil data history
            df = ticker.history(period=period, interval=interval, auto_adjust=False)

            # 1. Cek Apakah Data Kosong
            if df.empty:
                if period == "2y":
                    df = ticker.history(
                        period="max", interval=interval, auto_adjust=False
                    )

                if df.empty:
                    raise ValueError(f"Data kosong dari YFinance")

            # 2. Pembersihan Kolom & Timezone
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            # --- 🛠️ FIX DUPLICATE COLUMN: CLOSE VS ADJ CLOSE ---
            # Jika ada 'Adj Close', kita pakai itu sebagai acuan harga 'Close' sebenarnya.
            # TAPI, kita harus hapus kolom 'Close' bawaan dulu agar tidak ada 2 kolom bernama 'Close'.
            if "Adj Close" in df.columns:
                df = df.drop(columns=["Close"], errors="ignore")  # Hapus Close lama
                df = df.rename(
                    columns={"Adj Close": "Close"}
                )  # Rename Adj Close jadi Close

            # Rename kolom lain
            df = df.rename(columns={"Stock Splits": "Splits"})

            # Validasi kolom wajib
            required = ["Open", "High", "Low", "Close", "Volume"]
            for col in required:
                if col not in df.columns:
                    if col == "Volume":
                        df["Volume"] = 0
                    else:
                        raise ValueError(
                            f"Kolom wajib {col} hilang. Columns: {df.columns}"
                        )

            # 3. Cek Jumlah Data SEBELUM Indikator
            if len(df) < 60:
                raise ValueError(
                    f"Data mentah kurang ({len(df)} row), butuh min 60 row"
                )

            # 4. Hitung Indikator
            df.ta.rsi(length=14, append=True)
            df.ta.macd(append=True)
            df.ta.sma(length=20, append=True)
            df.ta.sma(length=50, append=True)
            df.ta.atr(length=14, append=True)
            # --- 🛠️ FIX ATR COLUMN NAME ---
            # pandas_ta sering menamai kolom ATR sebagai 'ATRr_14' (RMA)
            if "ATRr_14" in df.columns:
                df = df.rename(columns={"ATRr_14": "ATR_14"})

            # Debugging (Opsional): Cek kolom apa saja yang ada kalau masih error
            # logging.info(f"Columns in {symbol}: {df.columns.tolist()}")

            # 5. Drop NaN
            df_clean = df.dropna()

            # Pastikan tidak ada kolom duplikat tersisa (Safety Net)
            df_clean = df_clean.loc[:, ~df_clean.columns.duplicated()]

            # 6. Cek Akhir
            if df_clean.empty:
                raise ValueError(f"Data habis (0) setelah dropna.")

            return df_clean

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                logger.error(f"❌ GAGAL {symbol}: {e}")
                return pd.DataFrame()


def validate_data_quality(df):
    """
    Mencegah sampah masuk ke AI.
    Return: (bool, reason)
    """
    # 1. Cek Data Kosong / Sedikit
    if len(df) < 50:
        return False, "Not enough data points (<50)"

    # 2. Cek Flatline (Harga tidak bergerak sama sekali - Libur/Suspensi)
    last_5_candles = df["Close"].tail(5)
    if last_5_candles.nunique() == 1:
        return False, "Flatline Data (Market Closed/Suspended)"

    # 3. Cek Harga Nol/Negatif (Bug YFinance)
    if (df["Close"] <= 0).any():
        return False, "Zero/Negative Prices detected"

    # 4. Cek Gap Abnormal (Misal glitch harga naik 500% dalam 1 jam)
    # Gunakan pct_change
    returns = df["Close"].pct_change().dropna()
    max_change = returns.abs().max()
    if max_change > 0.5:  # 50% change in 1 hour is likely a glitch (except crypto pump)
        return False, f"Abnormal Spike Detected ({max_change*100:.0f}%)"

    return True, "OK"
