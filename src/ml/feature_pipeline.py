# src/ml/feature_pipeline.py
import pandas_ta as ta
import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler

from src.ml.feature_store_client import FeatureStoreClient


class FeaturePipeline:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.feature_client = FeatureStoreClient()

    def compute_technical_indicators(self, symbol: str):
        """Compute dan store technical indicators"""
        # Fetch latest data
        df = yf.download(symbol, period="1d", interval="5m")

        if df is None or df.empty:
            print(f"No data available for {symbol}")
            return

        # Calculate indicators
        df["rsi_14"] = ta.rsi(df["Close"], length=14)
        macd = ta.macd(df["Close"])
        df["macd_line"] = macd["MACD_12_26_9"]
        df["macd_signal"] = macd["MACDs_12_26_9"]

        # Store ke feature store
        self.feature_client.store_features(symbol, df)

    def start(self):
        """Start scheduled feature computation"""
        # Update setiap 5 menit
        self.scheduler.add_job(
            self.compute_technical_indicators, "interval", minutes=5, args=["BBCA.JK"]
        )
        self.scheduler.start()
