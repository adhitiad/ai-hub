# src/core/train_rf.py
import asyncio
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from src.core.data_loader import fetch_data_async
from src.core.database import assets_collection

# IMPORT BARU
from src.core.feature_enginering import enrich_data, get_model_input

MODEL_PATH = "models/rf_model.joblib"


def create_targets(df, lookahead=5, threshold=0.002):
    # (Logika target tetap sama)
    future_close = df["Close"].shift(-lookahead)
    change = (future_close - df["Close"]) / df["Close"]
    targets = (change > threshold).astype(int)
    return targets.iloc[:-lookahead]


async def train_classic_ml():
    print("🚀 Training Random Forest (Standardized)...")

    all_features = []
    all_targets = []

    symbols_cursor = assets_collection.find(
        {"type": {"$in": ["forex", "stock_indo", "crypto"]}}
    )
    symbols = await symbols_cursor.to_list(length=None)

    for symbol_doc in symbols:
        symbol = symbol_doc["symbol"]
        print(f"📥 Fetching {symbol}...")
        try:
            # 1. Fetch Raw Data
            df = await fetch_data_async(symbol, period="2y", interval="1h")
            if df.empty:
                continue

            # 2. Enrich Data (Pakai fungsi sentral)
            df_enriched = enrich_data(df)

            # 3. Create Targets (y)
            y_part = create_targets(df_enriched)

            # 4. Get Features (X) - Pakai fungsi sentral agar urutan baku
            X_part = get_model_input(df_enriched)

            # Align Index
            common_idx = X_part.index.intersection(y_part.index)
            all_features.append(X_part.loc[common_idx])
            all_targets.append(y_part.loc[common_idx])

        except Exception as e:
            print(f"⚠️ Skip {symbol}: {e}")

    if not all_features:
        print("❌ No data.")
        return

    X = pd.concat(all_features)
    y = pd.concat(all_targets)

    # Train
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    rf = RandomForestClassifier(
        n_estimators=100, max_depth=10, class_weight="balanced", random_state=42
    )
    rf.fit(X_train, y_train)

    print("\n📊 Evaluation:")
    print(classification_report(y_test, rf.predict(X_test)))

    os.makedirs("models", exist_ok=True)
    joblib.dump(rf, MODEL_PATH)
    print(f"✅ Model Saved: {MODEL_PATH}")


if __name__ == "__main__":
    asyncio.run(train_classic_ml())
