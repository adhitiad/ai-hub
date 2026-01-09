# src/core/ml_features.py
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from src.core.logger import logger

RF_MODEL_PATH = "models/rf_model.joblib"


class MarketMLAnalyzer:
    """
    Modul ML Klasik untuk memfilter sinyal dan mendeteksi rezim pasar.
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.rf_model = None
        self._load_rf_model()

    def _load_rf_model(self):
        """Load Pre-trained Random Forest jika ada"""
        if os.path.exists(RF_MODEL_PATH):
            try:
                self.rf_model = joblib.load(RF_MODEL_PATH)
                logger.info("🌲 Random Forest Model Loaded Successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load RF model: {e}")
        else:
            logger.warning(
                "⚠️ RF Model not found. Please run 'python src/core/train_rf.py'"
            )

    def analyze_trend_slope(self, df, period=20):
        """
        1. LINEAR REGRESSION: Menghitung kemiringan (slope) tren.
        Output:
         > 0.3 : Strong Uptrend
         < -0.3: Strong Downtrend
        """
        if len(df) < period:
            return 0.0

        # Ambil data Close terakhir
        y = df["Close"].tail(period).values.reshape(-1, 1)
        X = np.arange(len(y)).reshape(-1, 1)

        # Normalisasi agar slope tidak bias terhadap harga nominal
        y_norm = (y - y.min()) / (y.max() - y.min() + 1e-9)

        reg = LinearRegression().fit(X, y_norm)
        slope = reg.coef_[0][0] * 100  # Skalakan agar mudah dibaca
        return round(slope, 3)

    def detect_market_regime(self, df, period=50):
        """
        2. K-MEANS CLUSTERING: Deteksi kondisi pasar (Sideways vs Trending vs Volatile).
        Output:
         0: Low Volatility (Sideways/Aman)
         1: Normal Volatility (Trending)
         2: High Volatility (Bahaya/News)
        """
        if len(df) < period:
            return 1  # Default Normal

        # Fitur: ATR (Volatilitas) dan Volume
        data = df[["ATR_14", "Volume"]].tail(period).copy()
        data = data.fillna(0)

        # Scaling penting untuk K-Means
        scaled_data = self.scaler.fit_transform(data)

        # Clustering menjadi 3 kelompok
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        kmeans.fit(scaled_data)

        # Prediksi kondisi candle terakhir
        last_candle = scaled_data[-1].reshape(1, -1)
        cluster = kmeans.predict(last_candle)[0]

        # Mapping cluster ID ke makna sebenarnya berdasarkan rata-rata ATR
        data["cluster"] = kmeans.labels_
        cluster_avg_atr = data.groupby("cluster")["ATR_14"].mean().sort_values()

        # Mapping urutan: Low (0), Medium (1), High (2)
        regime_map = {idx: rank for rank, idx in enumerate(cluster_avg_atr.index)}

        return regime_map.get(cluster, 1)

    def rf_signal_confirmation(self, df):
        """
        3. RANDOM FOREST: Konfirmasi probabilitas kemenangan dari pola saat ini.
        Output: Score -100 s/d 100
        """
        if self.rf_model is None:
            return 0

        try:
            last = df.iloc[-1]

            # Hitung fitur on-the-fly (Sama dengan training)
            dist_sma20 = (last["Close"] - last.get("SMA_20", last["Close"])) / last.get(
                "SMA_20", 1
            )
            dist_sma50 = (last["Close"] - last.get("SMA_50", last["Close"])) / last.get(
                "SMA_50", 1
            )

            features = np.array(
                [
                    last.get("RSI_14", 50),
                    last.get("MACD_12_26_9", 0),
                    last.get("MACDh_12_26_9", 0),
                    last.get("ATR_14", 0),
                    dist_sma20,
                    dist_sma50,
                    last["Volume"],
                ]
            ).reshape(1, -1)

            if np.isnan(features).any() or np.isinf(features).any():
                return 0

            # Predict Probability Win (Index 1)
            win_prob = self.rf_model.predict_proba(features)[0][1]

            # Konversi ke Score (-100 s/d 100)
            score = (win_prob - 0.5) * 200
            return int(score)

        except Exception as e:
            logger.error(f"RF Prediction Error: {e}")
            return 0


# Instance global
ml_analyzer = MarketMLAnalyzer()
