# src/core/ml_features.py
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from train_rf import enrich_data, get_model_input

from src.core.feature_enginering import enrich_data, get_model_input
from src.core.logger import logger

RF_MODEL_PATH = "models/rf_model.joblib"


class MarketMLAnalyzer:
    def __init__(self):
        self.rf_model = None
        self._load_rf_model()
        self.scaler = StandardScaler()

    def _load_rf_model(self):
        if os.path.exists(RF_MODEL_PATH):
            try:
                self.rf_model = joblib.load(RF_MODEL_PATH)
            except Exception as e:
                logger.error(f"Error loading RF model: {e}")
                self.rf_model = None

    def reload_model(self):
        self._load_rf_model()

    def analyze_trend_slope(self, df, period=20):
        """Linear Regression Slope"""
        if len(df) < period:
            return 0.0

        y = df["Close"].tail(period).values.reshape(-1, 1)
        X = np.arange(len(y)).reshape(-1, 1)

        # Normalisasi min-max lokal agar slope tidak bias harga nominal
        y_min, y_max = y.min(), y.max()
        if y_max == y_min:
            return 0.0  # Hindari division by zero flat line

        y_norm = (y - y_min) / (y_max - y_min + 1e-9)

        reg = LinearRegression().fit(X, y_norm)
        slope = reg.coef_[0][0] * 100
        return round(slope, 3)

    def detect_market_regime(self, df, period=50):
        """K-Means Clustering untuk Volatilitas"""
        if len(df) < period:
            return 1

        # Gunakan ATR dan Volume sebagai fitur volatilitas
        # Pastikan kolom ada
        if "ATR_14" not in df.columns:
            return 1

        data = df[["ATR_14", "Volume"]].tail(period).copy().fillna(0)

        try:
            scaled_data = self.scaler.fit_transform(data)
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            kmeans.fit(scaled_data)

            last_candle = scaled_data[-1].reshape(1, -1)
            cluster = kmeans.predict(last_candle)[0]

            data["cluster"] = kmeans.labels_
            cluster_avg_atr = data.groupby("cluster")["ATR_14"].mean().sort_values()
            regime_map = {idx: rank for rank, idx in enumerate(cluster_avg_atr.index)}

            return regime_map.get(cluster, 1)
        except Exception as e:
            logger.error(f"KMeans Error: {e}")
            return 1

    def rf_signal_confirmation(self, df):
        """
        Menggunakan Fitur Sentral untuk Prediksi
        """
        if self.rf_model is None:
            return 0

        try:
            # 1. Pastikan DataFrame sudah diperkaya (Enriched)
            # Jika df belum punya kolom indikator, kita hitung dulu
            # (Tapi biasanya data_loader sudah panggil enrich, ini jaga-jaga)
            if "dist_sma20" not in df.columns:
                df = enrich_data(df)

            # 2. Ambil baris terakhir saja untuk prediksi live
            last_row_df = df.iloc[[-1]].copy()

            # 3. Format Fitur Sesuai Training (CRITICAL STEP)
            features_df = get_model_input(last_row_df)

            # Konversi ke numpy array
            features_array = features_df.values

            # 4. Predict
            win_prob = self.rf_model.predict_proba(features_array)[0][1]
            return int((win_prob - 0.5) * 200)

        except Exception as e:
            logger.error(f"RF Prediction Error: {e}")
            return 0


ml_analyzer = MarketMLAnalyzer()
