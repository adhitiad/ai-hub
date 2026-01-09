# src/core/train_rf.py

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from src.core.config_assets import ASSETS
from src.core.data_loader import fetch_data
from src.core.database import assets_collection

MODEL_PATH = "models/rf_model.joblib"


def prepare_features(df):
    """
    Menyiapkan fitur teknikal yang bersih untuk ML.
    HARUS SAMA PERSIS dengan yang ada di ml_features.py saat live.
    """
    df = df.copy()

    # 1. Feature Engineering
    # Jarak harga ke SMA (Trend Strength)
    df["dist_sma20"] = (df["Close"] - df["SMA_20"]) / df["SMA_20"]
    df["dist_sma50"] = (df["Close"] - df["SMA_50"]) / df["SMA_50"]

    # RSI & MACD sudah ada dari data_loader
    # Kita ambil fitur numerik saja
    features = [
        "RSI_14",
        "MACD_12_26_9",
        "MACDh_12_26_9",  # Histogram
        "ATR_14",
        "dist_sma20",
        "dist_sma50",
        "Volume",
    ]

    # Drop NaN akibat indikator (biasanya 50 baris pertama)
    df_clean = df[features].dropna()
    return df_clean, df


def create_targets(df, lookahead=5, threshold=0.002):
    """
    Membuat Label (Kunci Jawaban).
    Win (1) jika harga naik > 0.2% dalam 5 jam ke depan.
    """
    # Shift close price ke belakang (future price)
    future_close = df["Close"].shift(-lookahead)

    # Hitung persentase perubahan
    change = (future_close - df["Close"]) / df["Close"]

    # Label: 1 jika profit > threshold, 0 jika tidak
    targets = (change > threshold).astype(int)

    # Hapus baris terakhir yang NaN karena shift
    return targets.iloc[:-lookahead]


async def train_classic_ml():
    print("🚀 Training Random Forest for Pattern Recognition...")

    all_features = []
    all_targets = []

    # Ambil sampel aset utama (Forex & Saham) untuk generalisasi pola

    symbols_cursor = assets_collection.find({"type": {"$in": ["forex", "stock_indo"]}})
    symbols = await symbols_cursor.to_list(length=None)

    for symbol_doc in symbols:
        symbol = symbol_doc["symbol"]
        print(f"📥 Fetching data for {symbol}...")
        try:
            # Ambil data max (panjang)
            df = fetch_data(symbol, period="2y", interval="1h")
            if df.empty:
                continue

            # Siapkan Fitur & Target
            X_part, df_full = prepare_features(df)
            y_part = create_targets(df_full)

            # Align index (karena y_part lebih pendek akibat lookahead)
            common_idx = X_part.index.intersection(y_part.index)
            X_part = X_part.loc[common_idx]
            y_part = y_part.loc[common_idx]

            all_features.append(X_part)
            all_targets.append(y_part)

        except Exception as e:
            print(f"⚠️ Error {symbol}: {e}")

    # Gabung semua data
    if not all_features:
        print("❌ No data fetched.")
        return

    X = pd.concat(all_features)
    y = pd.concat(all_targets)

    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train Model
    # n_estimators=100 (100 pohon keputusan)
    # class_weight='balanced' (agar sensitif terhadap win yang jarang)
    rf = RandomForestClassifier(
        n_estimators=100, max_depth=10, class_weight="balanced", random_state=42
    )
    rf.fit(X_train, y_train)

    # Evaluasi
    print("\n📊 Evaluation Results:")
    print(classification_report(y_test, rf.predict(X_test)))

    # Simpan
    os.makedirs("models", exist_ok=True)
    joblib.dump(rf, MODEL_PATH)
    print(f"✅ Trained Model Saved: {MODEL_PATH}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(train_classic_ml())
